#!/usr/bin/env python3
"""
Static validation tests for CI-safe validation.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


pytestmark = pytest.mark.ci

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestPythonScripts:
    def test_populate_script_syntax(self):
        script = PROJECT_ROOT / "scripts" / "populate-gitlab.py"
        assert script.exists(), "populate-gitlab.py not found"

        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script)],
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr.decode()

    def test_test_files_syntax(self):
        test_files = list((PROJECT_ROOT / "tests").rglob("test_*.py"))
        assert test_files, "No test files found"

        for test_file in test_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(test_file)],
                capture_output=True,
            )
            assert result.returncode == 0, f"Syntax error in {test_file}: {result.stderr.decode()}"


class TestBashScripts:
    def test_setup_script_syntax(self):
        script = PROJECT_ROOT / "setup.sh"
        assert script.exists(), "setup.sh not found"

        result = subprocess.run(["bash", "-n", str(script)], capture_output=True)
        assert result.returncode == 0, result.stderr.decode()

    def test_setup_script_executable(self):
        script = PROJECT_ROOT / "setup.sh"
        assert os.access(script, os.X_OK), "setup.sh is not executable"


class TestConfigFiles:
    def test_base_yaml_valid(self):
        base_file = PROJECT_ROOT / "lab-config" / "base.yml"
        assert base_file.exists(), "base.yml not found"

        with open(base_file, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        assert data is not None, "base.yml is empty"
        assert "lab" in data
        assert "users" in data

    def test_scenarios_valid(self):
        scenarios_dir = PROJECT_ROOT / "lab-config" / "scenarios"
        assert scenarios_dir.exists(), "scenarios directory not found"

        scenario_files = list(scenarios_dir.glob("*.yml")) + list(scenarios_dir.glob("*.yaml"))
        assert scenario_files, "No scenario files found"

        for scenario_file in scenario_files:
            with open(scenario_file, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
            assert data is not None, f"{scenario_file.name} is empty"

    def test_merge_script_valid(self):
        merge_script = PROJECT_ROOT / "scripts" / "merge-scenarios.py"
        base_file = PROJECT_ROOT / "lab-config" / "base.yml"
        scenarios_dir = PROJECT_ROOT / "lab-config" / "scenarios"
        output_file = Path("/tmp/gitlab-lab-merged-static.yml")

        result = subprocess.run(
            [
                sys.executable,
                str(merge_script),
                "--base",
                str(base_file),
                "--scenarios",
                str(scenarios_dir),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert output_file.exists(), "Merged output file not created"

        with open(output_file, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        assert "lab" in data
        assert "users" in data
        assert "groups" in data
        assert "projects" in data

    def test_validate_ci_templates_script(self):
        validator = PROJECT_ROOT / "scripts" / "validate-ci-templates.py"
        result = subprocess.run(
            [sys.executable, str(validator)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_docker_compose_yaml_valid(self):
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml not found"

        with open(compose_file, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        assert data is not None, "docker-compose.yml is empty"
        assert "services" in data

    def test_env_example_exists(self):
        env_example = PROJECT_ROOT / ".env.example"
        assert env_example.exists(), ".env.example not found"

        content = env_example.read_text(encoding="utf-8")
        assert "GITLAB_ROOT_PASSWORD" in content
        assert "GITLAB_ADMIN_TOKEN" in content
        assert "GITLAB_HOST_URL" in content


class TestProjectStructure:
    def test_required_directories(self):
        for dir_name in ["scripts", "lab-config", "tests", "pentester", "tools"]:
            dir_path = PROJECT_ROOT / dir_name
            assert dir_path.exists(), f"Required directory '{dir_name}' not found"
            assert dir_path.is_dir(), f"'{dir_name}' is not a directory"

    def test_required_files(self):
        required_files = [
            "setup.sh",
            "Makefile",
            "docker-compose.yml",
            ".env.example",
            "README.md",
            "pytest.ini",
            "lab-config/base.yml",
            "lab-config/scenarios/default.yml",
            "scripts/populate-gitlab.py",
            "scripts/merge-scenarios.py",
            "tools/webhook-logger/server.js",
        ]

        for file_path in required_files:
            full_path = PROJECT_ROOT / file_path
            assert full_path.exists(), f"Required file '{file_path}' not found"
            assert full_path.is_file(), f"'{file_path}' is not a file"

    def test_makefile_targets(self):
        makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
        for target in ["setup", "start", "stop", "destroy", "test-ci", "test-deployment"]:
            assert f"{target}:" in makefile, f"Makefile missing target '{target}'"
