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
    
    def test_structure_yaml_valid(self):
        """Verify structure.yml is valid YAML"""
        config_file = PROJECT_ROOT / "lab-config" / "structure.yml"
        assert config_file.exists(), "structure.yml not found"
        
        with open(config_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "structure.yml is empty"
                assert 'lab' in data, "Missing 'lab' section in structure.yml"
                assert 'users' in data, "Missing 'users' section in structure.yml"
                assert 'groups' in data, "Missing 'groups' section in structure.yml"
                assert 'projects' in data, "Missing 'projects' section in structure.yml"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in structure.yml: {e}")
    
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
            'lab-config/structure.yml',
            'scripts/populate-gitlab.py'
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
    
    def test_structure_has_valid_users(self):
        """Verify structure.yml has properly configured users"""
        config_file = PROJECT_ROOT / "lab-config" / "structure.yml"
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
            users = data.get('users', [])
            
            assert len(users) > 0, "No users defined in structure.yml"
            
            for user in users:
                assert 'username' in user, f"User missing username: {user}"
                assert 'email' in user, f"User {user.get('username')} missing email"
                assert 'password' in user, f"User {user.get('username')} missing password"
    
    def test_structure_has_valid_projects(self):
        """Verify structure.yml has properly configured projects"""
        config_file = PROJECT_ROOT / "lab-config" / "structure.yml"
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
            projects = data.get('projects', [])
            
            assert len(projects) > 0, "No projects defined in structure.yml"
            
            for project in projects:
                assert 'name' in project, f"Project missing name: {project}"
                assert 'path' in project, f"Project {project.get('name')} missing path"
                assert 'group' in project, f"Project {project.get('name')} missing group"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
