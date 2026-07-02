#!/usr/bin/env python3
"""
Validate Runners and Scenario Readiness
Verifies that all runners are operational and critical CI jobs have run
"""

import sys
import os
import time
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import gitlab
from gitlab.exceptions import GitlabGetError, GitlabCreateError


class RunnerValidator:
    def __init__(self, gitlab_url: str, admin_token: str):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.admin_token = admin_token
        self.session = requests.Session()
        self.session.headers.update({"PRIVATE-TOKEN": admin_token})
        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=admin_token)
        self.results = {
            "runner_health": {},
            "job_triggers": {},
            "artifact_checks": {},
            "scenario_readiness": {}
        }

    def log(self, level: str, message: str):
        """Log with colored output"""
        colors = {"INFO": "\033[94m", "OK": "\033[92m", "WARN": "\033[93m", "ERROR": "\033[91m", "RESET": "\033[0m"}
        color = colors.get(level, "")
        reset = colors["RESET"]
        print(f"[{level:>5}] {color}{message}{reset}")

    def check_runners_online(self) -> bool:
        """Verify at least one runner of each type is online"""
        self.log("INFO", "Checking runner status...")
        
        try:
            resp = self.session.get(f"{self.gitlab_url}/api/v4/runners/all", params={"per_page": 100}, timeout=10)
            resp.raise_for_status()
            runners = resp.json()
        except Exception as e:
            self.log("ERROR", f"Failed to fetch runners: {e}")
            return False

        docker_online = False
        shell_online = False

        for runner in runners:
            if runner.get("status") == "online":
                desc = runner.get("description", "")
                tags = set(runner.get("tag_list", []))
                
                if "docker" in tags and not docker_online:
                    docker_online = True
                    self.log("OK", f"Docker runner online: {desc}")
                elif "shell" in tags and not shell_online:
                    shell_online = True
                    self.log("OK", f"Shell runner online: {desc}")

        self.results["runner_health"]["docker_online"] = docker_online
        self.results["runner_health"]["shell_online"] = shell_online

        if docker_online and shell_online:
            self.log("OK", "All runner types online")
            return True
        else:
            self.log("WARN", f"Not all runners online: docker={docker_online}, shell={shell_online}")
            return False

    def trigger_test_jobs(self) -> bool:
        """Trigger simple test jobs on each runner to verify execution"""
        self.log("INFO", "Triggering runner test jobs...")
        
        test_projects = [
            ("security-tools", "docker"),  # Scenario 0
            ("qa-automation", "shell"),     # Scenario 1
        ]
        
        for project_path, runner_type in test_projects:
            try:
                project = self.gl.projects.get(project_path)
                
                # Trigger a pipeline
                pipeline = project.pipelines.create(
                    {"ref": "main"},
                    lazy=True  # Don't auto-fetch, just create
                )
                
                self.log("OK", f"Triggered pipeline on {project_path} (ID: {pipeline.id})")
                self.results["job_triggers"][project_path] = {"pipeline_id": pipeline.id, "runner_type": runner_type}
                
            except GitlabCreateError as e:
                self.log("WARN", f"Failed to trigger pipeline on {project_path}: {e}")
                self.results["job_triggers"][project_path] = {"error": str(e)}
            except Exception as e:
                self.log("WARN", f"Error triggering {project_path}: {e}")
                self.results["job_triggers"][project_path] = {"error": str(e)}
        
        return True

    def trigger_critical_jobs(self) -> bool:
        """Trigger critical jobs needed for scenario play-through"""
        self.log("INFO", "Triggering critical scenario jobs...")
        
        critical_projects = [
            ("web-service", "Scenario 02 - Lateral Movement (needs build_env.txt artifact)"),
            ("private-test-data", "Scenario 02 - Flag validation"),
            ("private-app", "Scenario 03 - Renovate bot exploitation"),
        ]
        
        for project_path, description in critical_projects:
            try:
                project = self.gl.projects.get(project_path)
                
                # Trigger pipeline
                pipeline = project.pipelines.create({"ref": "main"}, lazy=True)
                
                self.log("OK", f"Triggered {project_path}: {description} (ID: {pipeline.id})")
                self.results["job_triggers"][project_path] = {
                    "pipeline_id": pipeline.id,
                    "description": description
                }
                
            except GitlabCreateError as e:
                self.log("WARN", f"Failed to trigger {project_path}: {e}")
                self.results["job_triggers"][project_path] = {"error": str(e)}
            except GitlabGetError:
                self.log("WARN", f"Project {project_path} not found")
                self.results["job_triggers"][project_path] = {"error": "not_found"}
            except Exception as e:
                self.log("WARN", f"Error triggering {project_path}: {e}")
                self.results["job_triggers"][project_path] = {"error": str(e)}
        
        return True

    def wait_for_jobs(self, timeout_seconds: int = 600) -> bool:
        """Poll for job completion up to timeout"""
        self.log("INFO", f"Waiting for jobs to complete (timeout: {timeout_seconds}s)...")
        
        start_time = time.time()
        poll_interval = 5
        last_status = {}
        
        while time.time() - start_time < timeout_seconds:
            all_done = True
            some_running = False
            
            for project_path, job_info in self.results["job_triggers"].items():
                if "error" in job_info or "not_found" in job_info:
                    continue
                
                pipeline_id = job_info.get("pipeline_id")
                if not pipeline_id:
                    continue
                
                try:
                    project = self.gl.projects.get(project_path)
                    pipeline = project.pipelines.get(pipeline_id)
                    status = pipeline.status
                    
                    # Log status changes
                    if last_status.get(project_path) != status:
                        self.log("INFO", f"  {project_path}: {status}")
                        last_status[project_path] = status
                    
                    if status in ("pending", "running"):
                        all_done = False
                        some_running = True
                    elif status in ("success", "failed"):
                        job_info["final_status"] = status
                    
                except Exception as e:
                    self.log("WARN", f"Error checking {project_path} status: {e}")
            
            if all_done:
                self.log("OK", "All jobs completed")
                return True
            
            if not some_running:
                time.sleep(poll_interval)
                continue
            
            time.sleep(poll_interval)
        
        self.log("WARN", f"Job polling timed out after {timeout_seconds}s")
        return False

    def check_required_artifacts(self) -> bool:
        """Verify critical artifacts exist"""
        self.log("INFO", "Checking for required artifacts...")
        
        required_artifacts = {
            "web-service": ["build_env.txt"],
            "private-test-data": ["flags.txt"],
            "private-app": ["renovate-execution.log"],  # May not exist, log output is ok
        }
        
        all_present = True
        
        for project_path, artifacts in required_artifacts.items():
            try:
                project = self.gl.projects.get(project_path)
                pipelines = project.pipelines.list(status="success", order_by="updated_at", sort="desc", per_page=1)
                
                if not pipelines:
                    self.log("WARN", f"{project_path}: No successful pipelines found")
                    self.results["artifact_checks"][project_path] = {"status": "no_pipeline"}
                    all_present = False
                    continue
                
                latest_pipeline = pipelines[0]
                pipeline = project.pipelines.get(latest_pipeline.id)
                jobs = pipeline.jobs.list(all=True)
                
                found_artifacts = []
                for job in jobs:
                    job_detail = project.jobs.get(job.id)
                    artifacts_list = job_detail.artifacts
                    
                    if artifacts_list:
                        for artifact in artifacts_list:
                            found_artifacts.append(artifact.get("file_format", "artifact"))
                
                if found_artifacts:
                    self.log("OK", f"{project_path}: Found artifacts")
                    self.results["artifact_checks"][project_path] = {"artifacts": found_artifacts}
                else:
                    self.log("WARN", f"{project_path}: No artifacts found in successful pipeline")
                    self.results["artifact_checks"][project_path] = {"status": "no_artifacts"}
                    # web-service build_env.txt is critical
                    if project_path == "web-service":
                        all_present = False
            
            except GitlabGetError:
                self.log("WARN", f"{project_path}: Project not found")
                self.results["artifact_checks"][project_path] = {"status": "not_found"}
            except Exception as e:
                self.log("WARN", f"{project_path}: Error checking artifacts: {e}")
                self.results["artifact_checks"][project_path] = {"error": str(e)}
        
        return all_present

    def validate_scenario_readiness(self) -> Dict[str, bool]:
        """Check if each scenario is ready to play"""
        self.log("INFO", "Validating scenario readiness...")
        
        scenarios = {
            "scenario-00-getting-started": {
                "project": "security-tools",
                "required": [],  # No artifacts needed
                "notes": "Ready immediately"
            },
            "scenario-01-cicd-variables-exposure": {
                "project": "qa-automation",
                "required": [],
                "notes": "Ready immediately"
            },
            "scenario-02-lateral-movement": {
                "project": "web-service",
                "required": ["build_env.txt"],
                "notes": "Requires build_env.txt artifact from web-service build job"
            },
            "scenario-03-renovate-bot-exploitation": {
                "project": "private-app",
                "required": [],
                "notes": "Requires pentester-renovate-poc project to be created by attacker"
            },
            "scenario-04-runner-abuse": {
                "project": "runner-breakout-lab",
                "required": [],
                "notes": "Depends on scheduled jobs (payroll-batch, telemetry-batch run every 5-7 min)"
            }
        }
        
        readiness = {}
        
        for scenario_name, config in scenarios.items():
            ready = True
            blockers = []
            
            project_path = config["project"]
            required_artifacts = config["required"]
            
            # Check if project exists
            try:
                project = self.gl.projects.get(project_path)
            except GitlabGetError:
                ready = False
                blockers.append(f"Project {project_path} not found")
                self.log("ERROR", f"{scenario_name}: Project {project_path} not found")
                readiness[scenario_name] = {"ready": False, "blockers": blockers}
                continue
            
            # Check for required artifacts
            for artifact_name in required_artifacts:
                artifact_check = self.results["artifact_checks"].get(project_path, {})
                if "status" in artifact_check and artifact_check["status"] in ("no_artifacts", "no_pipeline"):
                    ready = False
                    blockers.append(f"Missing artifact: {artifact_name}")
            
            status_str = "READY ✓" if ready else "BLOCKED ⚠"
            self.log("OK", f"{scenario_name}: {status_str}")
            
            if blockers:
                for blocker in blockers:
                    self.log("WARN", f"  └─ {blocker}")
            
            readiness[scenario_name] = {
                "ready": ready,
                "blockers": blockers,
                "notes": config["notes"]
            }
        
        self.results["scenario_readiness"] = readiness
        return readiness

    def run_validation(self, timeout_seconds: int = 600) -> Tuple[bool, Dict]:
        """Run complete validation suite"""
        self.log("INFO", "Starting runner and scenario validation...")
        print()
        
        # Phase 1: Check runners are online
        if not self.check_runners_online():
            self.log("ERROR", "Runners not online - setup cannot proceed")
            return False, self.results
        
        print()
        
        # Phase 2: Trigger test and critical jobs
        self.trigger_test_jobs()
        self.trigger_critical_jobs()
        
        print()
        
        # Phase 3: Wait for jobs to complete
        if not self.wait_for_jobs(timeout_seconds):
            self.log("WARN", "Job execution timed out")
        
        print()
        
        # Phase 4: Check artifacts
        self.check_required_artifacts()
        
        print()
        
        # Phase 5: Validate scenario readiness
        readiness = self.validate_scenario_readiness()
        
        print()
        
        # Determine overall success
        blocked_scenarios = [s for s, r in readiness.items() if not r["ready"]]
        
        if blocked_scenarios:
            self.log("WARN", f"{len(blocked_scenarios)} scenarios blocked:")
            for scenario in blocked_scenarios:
                for blocker in readiness[scenario]["blockers"]:
                    self.log("WARN", f"  • {scenario}: {blocker}")
            return False, self.results
        else:
            self.log("OK", "All scenarios ready for play-through!")
            return True, self.results


def main():
    gitlab_url = os.environ.get("GITLAB_HOST_URL", "http://127.0.0.1:8081").rstrip('/')
    admin_token = os.environ.get("GITLAB_ADMIN_TOKEN", "")
    timeout = int(os.environ.get("VALIDATION_TIMEOUT", "600"))
    
    if not admin_token:
        print("[ERROR] GITLAB_ADMIN_TOKEN not set")
        sys.exit(1)
    
    validator = RunnerValidator(gitlab_url, admin_token)
    
    try:
        success, results = validator.run_validation(timeout_seconds=timeout)
        
        # Print summary
        print("\n" + "=" * 70)
        if success:
            print("✓ VALIDATION PASSED - Lab is ready for scenario play-through")
            print("=" * 70)
            sys.exit(0)
        else:
            print("✗ VALIDATION FAILED - Some scenarios are not yet ready")
            print("  Check the logs above for details and try running setup again")
            print("=" * 70)
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n[INFO] Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
