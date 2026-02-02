#!/usr/bin/env python3
"""
Static validation tests for CI/CD
These tests validate code syntax and configuration without requiring GitLab to run.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class TestPythonScripts:
    """Validate Python scripts for syntax errors"""
    
    def test_populate_script_syntax(self):
        """Verify populate-gitlab.py has valid Python syntax"""
        script = PROJECT_ROOT / "scripts" / "populate-gitlab.py"
        assert script.exists(), "populate-gitlab.py not found"
        
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script)],
            capture_output=True
        )
        assert result.returncode == 0, f"Syntax error in populate-gitlab.py: {result.stderr.decode()}"
    
    def test_populate_script_imports(self):
        """Verify populate-gitlab.py dependencies are available"""
        # Test that required modules can be imported
        result = subprocess.run(
            [sys.executable, "-c", "import requests; import yaml"],
            capture_output=True
        )
        assert result.returncode == 0, f"Import error: {result.stderr.decode()}"
    
    def test_test_files_syntax(self):
        """Verify all test files have valid syntax"""
        test_files = list((PROJECT_ROOT / "tests").glob("test_*.py"))
        assert len(test_files) > 0, "No test files found"
        
        for test_file in test_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(test_file)],
                capture_output=True
            )
            assert result.returncode == 0, f"Syntax error in {test_file.name}: {result.stderr.decode()}"


class TestBashScripts:
    """Validate bash scripts for syntax errors"""
    
    def test_setup_script_syntax(self):
        """Verify setup.sh has valid bash syntax"""
        script = PROJECT_ROOT / "setup.sh"
        assert script.exists(), "setup.sh not found"
        
        result = subprocess.run(
            ["bash", "-n", str(script)],
            capture_output=True
        )
        assert result.returncode == 0, f"Syntax error in setup.sh: {result.stderr.decode()}"
    
    def test_setup_script_executable(self):
        """Verify setup.sh is executable"""
        script = PROJECT_ROOT / "setup.sh"
        assert os.access(script, os.X_OK), "setup.sh is not executable"


class TestConfigFiles:
    """Validate configuration files"""
    
    def test_base_yaml_valid(self):
        """Verify base.yml is valid YAML"""
        base_file = PROJECT_ROOT / "lab-config" / "base.yml"
        assert base_file.exists(), "base.yml not found"
        
        with open(base_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "base.yml is empty"
                assert 'lab' in data, "Missing 'lab' section in base.yml"
                assert 'users' in data, "Missing 'users' section in base.yml"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in base.yml: {e}")

    def test_scenarios_valid(self):
        """Verify scenario files are valid YAML"""
        scenarios_dir = PROJECT_ROOT / "lab-config" / "scenarios"
        assert scenarios_dir.exists(), "scenarios directory not found"
        scenario_files = list(scenarios_dir.glob("*.yml")) + list(scenarios_dir.glob("*.yaml"))
        assert len(scenario_files) > 0, "No scenario files found"

        for scenario_file in scenario_files:
            with open(scenario_file, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    assert data is not None, f"{scenario_file.name} is empty"
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {scenario_file.name}: {e}")

    def test_merge_script_valid(self):
        """Verify merge-scenarios script can produce a merged config"""
        merge_script = PROJECT_ROOT / "scripts" / "merge-scenarios.py"
        base_file = PROJECT_ROOT / "lab-config" / "base.yml"
        scenarios_dir = PROJECT_ROOT / "lab-config" / "scenarios"
        output_file = Path("/tmp/gitlab-lab-merged-static.yml")
        
        result = subprocess.run(
            [
                "python3", str(merge_script),
                "--base", str(base_file),
                "--scenarios", str(scenarios_dir),
                "--output", str(output_file)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Merge failed: {result.stderr}"
        assert output_file.exists(), "Merged output file not created"

        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)
            assert 'lab' in data, "Missing 'lab' in merged config"
            assert 'users' in data, "Missing 'users' in merged config"
            assert 'groups' in data, "Missing 'groups' in merged config"
            assert 'projects' in data, "Missing 'projects' in merged config"

    def test_docker_compose_yaml_valid(self):
        """Verify docker-compose.yml is valid YAML"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml not found"
        
        with open(compose_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "docker-compose.yml is empty"
                assert 'services' in data, "Missing 'services' in docker-compose.yml"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in docker-compose.yml: {e}")
    
    def test_env_example_exists(self):
        """Verify .env.example file exists"""
        env_example = PROJECT_ROOT / ".env.example"
        assert env_example.exists(), ".env.example not found"
        
        with open(env_example, 'r') as f:
            content = f.read()
            assert 'GITLAB_ROOT_PASSWORD' in content, "Missing GITLAB_ROOT_PASSWORD in .env.example"
            assert 'GITLAB_ADMIN_TOKEN' in content, "Missing GITLAB_ADMIN_TOKEN in .env.example"


class TestProjectStructure:
    """Validate project structure and required files"""
    
    def test_required_directories(self):
        """Verify all required directories exist"""
        required_dirs = [
            'scripts',
            'lab-config',
            'tests',
            'data',
            'pentester'
        ]
        
        for dir_name in required_dirs:
            dir_path = PROJECT_ROOT / dir_name
            assert dir_path.exists(), f"Required directory '{dir_name}' not found"
            assert dir_path.is_dir(), f"'{dir_name}' is not a directory"
    
    def test_required_files(self):
        """Verify all required files exist"""
        required_files = [
            'setup.sh',
            'Makefile',
            'docker-compose.yml',
            '.env.example',
            'README.md',
            'lab-config/base.yml',
            'lab-config/scenarios/default.yml',
            'scripts/populate-gitlab.py',
            'scripts/merge-scenarios.py'
        ]
        
        for file_path in required_files:
            full_path = PROJECT_ROOT / file_path
            assert full_path.exists(), f"Required file '{file_path}' not found"
            assert full_path.is_file(), f"'{file_path}' is not a file"
    
    def test_makefile_targets(self):
        """Verify Makefile has required targets"""
        makefile = PROJECT_ROOT / "Makefile"
        
        with open(makefile, 'r') as f:
            content = f.read()
            required_targets = ['setup', 'start', 'stop', 'destroy', 'help']
            
            for target in required_targets:
                assert f"{target}:" in content, f"Makefile missing required target '{target}'"


class TestDataFiles:
    """Validate data and configuration files"""
    
    def _load_merged_config(self):
        merge_script = PROJECT_ROOT / "scripts" / "merge-scenarios.py"
        base_file = PROJECT_ROOT / "lab-config" / "base.yml"
        scenarios_dir = PROJECT_ROOT / "lab-config" / "scenarios"
        output_file = Path("/tmp/gitlab-lab-merged-static.yml")

        result = subprocess.run(
            [
                "python3", str(merge_script),
                "--base", str(base_file),
                "--scenarios", str(scenarios_dir),
                "--output", str(output_file)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Merge failed: {result.stderr}"

        with open(output_file, 'r') as f:
            return yaml.safe_load(f)

    def test_merged_has_valid_users(self):
        """Verify merged config has properly configured users"""
        data = self._load_merged_config()
        users = data.get('users', [])

        assert len(users) > 0, "No users defined in merged config"

        for user in users:
            assert 'username' in user, f"User missing username: {user}"
            assert 'email' in user, f"User {user.get('username')} missing email"
            assert 'password' in user, f"User {user.get('username')} missing password"
    
    def test_merged_has_valid_projects(self):
        """Verify merged config has properly configured projects"""
        data = self._load_merged_config()
        projects = data.get('projects', [])

        assert len(projects) > 0, "No projects defined in merged config"

        for project in projects:
            assert 'name' in project, f"Project missing name: {project}"
            assert 'path' in project, f"Project {project.get('name')} missing path"
            assert 'group' in project, f"Project {project.get('name')} missing group"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
