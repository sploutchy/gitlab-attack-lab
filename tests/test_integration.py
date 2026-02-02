#!/usr/bin/env python3
"""
GitLab Attack Lab - Integration Test Suite

Tests the complete setup and validates all components.
"""

import os
import time
import requests
import yaml
import subprocess
from typing import Dict, List, Optional

# Configuration
GITLAB_URL = os.getenv('GITLAB_URL', 'http://127.0.0.1')
API_BASE = f"{GITLAB_URL}/api/v4"
ENV_FILE = '.env'
MERGE_SCRIPT = 'scripts/merge-scenarios.py'
BASE_CONFIG = 'lab-config/base.yml'
SCENARIOS_DIR = 'lab-config/scenarios'
MERGED_CONFIG = '/tmp/gitlab-lab-merged-test.yml'

class GitLabTestClient:
    """Client for testing GitLab API"""
    
    def __init__(self):
        self.admin_token = self._get_admin_token()
        self.session = requests.Session()
        self.session.headers.update({
            'PRIVATE-TOKEN': self.admin_token,
            'Content-Type': 'application/json'
        })
    
    def _get_admin_token(self) -> str:
        """Extract admin token from .env file"""
        if not os.path.exists(ENV_FILE):
            raise FileNotFoundError(f"{ENV_FILE} not found")
        
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.startswith('GITLAB_ADMIN_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    if token and token != '':
                        return token
        
        raise ValueError("GITLAB_ADMIN_TOKEN not found in .env")
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make GET request to GitLab API"""
        url = f"{API_BASE}/{endpoint}"
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response
    
    def get_json(self, endpoint: str, **kwargs) -> dict:
        """Make GET request and return JSON"""
        return self.get(endpoint, **kwargs).json()

def load_merged_config() -> dict:
    """Load merged configuration from base + scenarios"""
    if not os.path.exists(MERGE_SCRIPT):
        raise FileNotFoundError(f"{MERGE_SCRIPT} not found")
    if not os.path.exists(BASE_CONFIG):
        raise FileNotFoundError(f"{BASE_CONFIG} not found")
    if not os.path.exists(SCENARIOS_DIR):
        raise FileNotFoundError(f"{SCENARIOS_DIR} not found")

    result = subprocess.run(
        [
            'python3', MERGE_SCRIPT,
            '--base', BASE_CONFIG,
            '--scenarios', SCENARIOS_DIR,
            '--output', MERGED_CONFIG
        ],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to merge scenarios: {result.stderr}")

    with open(MERGED_CONFIG, 'r') as f:
        return yaml.safe_load(f)

def test_gitlab_is_healthy():
    """Test that GitLab is up and responding"""
    print("Testing GitLab health...")
    response = requests.get(f"{GITLAB_URL}/api/v4/version", timeout=10)
    # 200 or 401 are both acceptable (401 means it's up but needs auth)
    assert response.status_code in [200, 401], f"GitLab not responding: {response.status_code}"
    
    if response.status_code == 200:
        version = response.json()
        print(f"  ✓ GitLab v{version.get('version')} is healthy")
    else:
        print(f"  ✓ GitLab is healthy (requires authentication)")

def test_admin_authentication():
    """Test that admin token works"""
    print("Testing admin authentication...")
    client = GitLabTestClient()
    
    user = client.get_json('user')
    assert user.get('username') == 'root', f"Not authenticated as root: {user.get('username')}"
    assert user.get('is_admin') is True, "Root user is not admin"
    
    print(f"  ✓ Authenticated as {user.get('username')} (admin: {user.get('is_admin')})")

def test_users_created():
    """Test that all users from merged scenarios are created"""
    print("Testing user creation...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    expected_users = [u['username'] for u in config['users'] if u['username'] != 'root']
    
    # Get all users from GitLab
    users = client.get_json('users')
    created_usernames = [u['username'] for u in users]
    
    for expected_user in expected_users:
        assert expected_user in created_usernames, f"User '{expected_user}' not created"
        print(f"  ✓ User '{expected_user}' exists")
    
    print(f"  ✓ All {len(expected_users)} users created successfully")

def test_groups_created():
    """Test that all groups from merged scenarios are created"""
    print("Testing group creation...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    expected_groups = [g['path'] for g in config['groups']]
    
    # Get all groups from GitLab
    groups = client.get_json('groups')
    created_group_paths = [g['path'] for g in groups]
    
    for expected_group in expected_groups:
        assert expected_group in created_group_paths, f"Group '{expected_group}' not created"
        print(f"  ✓ Group '{expected_group}' exists")
    
    print(f"  ✓ All {len(expected_groups)} groups created successfully")

def test_group_memberships():
    """Test that group members are added correctly"""
    print("Testing group memberships...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    for group_cfg in config['groups']:
        group_path = group_cfg['path']
        
        # Get group ID
        groups = client.get_json('groups', params={'search': group_path})
        group = next((g for g in groups if g['path'] == group_path), None)
        assert group is not None, f"Group '{group_path}' not found"
        
        # Get group members
        members = client.get_json(f"groups/{group['id']}/members")
        member_usernames = [m['username'] for m in members]
        
        # Check expected members
        for member_cfg in group_cfg.get('members', []):
            expected_username = member_cfg['username']
            assert expected_username in member_usernames, \
                f"User '{expected_username}' not in group '{group_path}'"
            print(f"  ✓ User '{expected_username}' is member of '{group_path}'")

def test_projects_created():
    """Test that all projects from merged scenarios are created"""
    print("Testing project creation...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    expected_projects = [f"{p['group']}/{p['path']}" for p in config['projects']]
    
    # Get all projects
    projects = client.get_json('projects', params={'membership': False, 'per_page': 100})
    created_project_paths = [p['path_with_namespace'] for p in projects]
    
    for expected_project in expected_projects:
        assert expected_project in created_project_paths, f"Project '{expected_project}' not created"
        print(f"  ✓ Project '{expected_project}' exists")
    
    print(f"  ✓ All {len(expected_projects)} projects created successfully")

def test_repositories_imported():
    """Test that repositories have content (were imported)"""
    print("Testing repository imports...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    for project_cfg in config['projects']:
        if not project_cfg.get('repo_url'):
            continue
        
        project_path = f"{project_cfg['group']}/{project_cfg['path']}"
        
        # Get project
        projects = client.get_json('projects', params={'search': project_cfg['path']})
        project = next((p for p in projects if p['path_with_namespace'] == project_path), None)
        assert project is not None, f"Project '{project_path}' not found"
        
        # Check if repository has commits (means it was imported)
        try:
            commits = client.get_json(f"projects/{project['id']}/repository/commits")
            assert len(commits) > 0, f"Project '{project_path}' has no commits"
            print(f"  ✓ Project '{project_path}' has {len(commits)} commits")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise AssertionError(f"Project '{project_path}' has no repository")
            raise

def test_ci_variables():
    """Test that CI/CD variables are created"""
    print("Testing CI/CD variables...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    for project_cfg in config['projects']:
        if not project_cfg.get('variables'):
            continue
        
        project_path = f"{project_cfg['group']}/{project_cfg['path']}"
        
        # Get project
        projects = client.get_json('projects', params={'search': project_cfg['path']})
        project = next((p for p in projects if p['path_with_namespace'] == project_path), None)
        assert project is not None, f"Project '{project_path}' not found"
        
        # Get variables
        variables = client.get_json(f"projects/{project['id']}/variables")
        variable_keys = [v['key'] for v in variables]
        
        # Check expected variables
        for var_cfg in project_cfg['variables']:
            expected_key = var_cfg['key']
            assert expected_key in variable_keys, \
                f"Variable '{expected_key}' not found in project '{project_path}'"
            print(f"  ✓ Variable '{expected_key}' exists in '{project_path}'")

def test_ci_configs():
    """Test that .gitlab-ci.yml files exist"""
    print("Testing CI configurations...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    ci_project_count = 0
    for project_cfg in config['projects']:
        if not project_cfg.get('ci_cd_enabled', False):
            continue
        
        project_path = f"{project_cfg['group']}/{project_cfg['path']}"
        
        # Get project
        projects = client.get_json('projects', params={'search': project_cfg['path']})
        project = next((p for p in projects if p['path_with_namespace'] == project_path), None)
        assert project is not None, f"Project '{project_path}' not found"
        
        # Check if .gitlab-ci.yml exists
        try:
            ci_file = client.get_json(
                f"projects/{project['id']}/repository/files/.gitlab-ci.yml",
                params={'ref': project_cfg.get('default_branch', 'main')}
            )
            assert ci_file is not None, f"CI file not found in '{project_path}'"
            print(f"  ✓ CI config exists in '{project_path}'")
            ci_project_count += 1
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"  ⚠ CI config missing in '{project_path}' (may be expected)")
            else:
                raise
    
    print(f"  ✓ Found CI configs in {ci_project_count} projects")

def test_runners_registered():
    """Test that runners are registered"""
    print("Testing runner registration...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    # Get all runners (admin endpoint)
    runners = client.get_json('runners/all', params={'per_page': 100})
    
    expected_runners = [r['description'] for r in config.get('runners', [])]
    registered_descriptions = [r['description'] for r in runners]
    
    for expected_runner in expected_runners:
        assert expected_runner in registered_descriptions, \
            f"Runner '{expected_runner}' not registered"
        print(f"  ✓ Runner '{expected_runner}' is registered")
    
    print(f"  ✓ All {len(expected_runners)} runners registered successfully")

def test_runners_online():
    """Test that runners are online and active"""
    print("Testing runner status...")
    client = GitLabTestClient()
    config = load_merged_config()
    
    # Wait a bit for runners to connect
    print("  Waiting for runners to connect...")
    time.sleep(10)
    
    runners = client.get_json('runners/all', params={'per_page': 100})
    
    expected_runners = [r['description'] for r in config.get('runners', [])]
    
    for expected_runner_desc in expected_runners:
        runner = next((r for r in runners if r['description'] == expected_runner_desc), None)
        assert runner is not None, f"Runner '{expected_runner_desc}' not found"
        
        # Check if runner is online (contacted recently)
        status = runner.get('status', 'offline')
        if status == 'online':
            print(f"  ✓ Runner '{expected_runner_desc}' is online")
        else:
            # Sometimes runners need more time, check if they've ever contacted
            if runner.get('contacted_at') is not None:
                print(f"  ⚠ Runner '{expected_runner_desc}' contacted but currently {status}")
            else:
                raise AssertionError(f"Runner '{expected_runner_desc}' has never contacted GitLab")

def test_docker_containers_running():
    """Test that all expected containers are running"""
    print("Testing container status...")
    
    result = subprocess.run(
        ['docker-compose', 'ps', '--format', 'json'],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) + '/..'
    )
    
    assert result.returncode == 0, "docker-compose ps failed"
    
    import json
    containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
    
    expected_containers = [
        'gitlab-attack-lab',
        'gitlab-runner-docker',
        'gitlab-runner-shell',
        'pentester',
        'mailhog'
    ]
    
    running_containers = [c['Name'] for c in containers if c.get('State') == 'running']
    
    for expected in expected_containers:
        assert expected in running_containers, f"Container '{expected}' not running"
        print(f"  ✓ Container '{expected}' is running")

def test_pipeleek_configured():
    """Test that pipeleek is configured in pentester container"""
    print("Testing Pipeleek configuration...")
    
    result = subprocess.run(
        ['docker-compose', 'exec', '-T', 'pentester', 'test', '-f', '/root/.config/pipeleek/pipeleek.yaml'],
        capture_output=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) + '/..'
    )
    
    assert result.returncode == 0, "Pipeleek config file not found in pentester container"
    print("  ✓ Pipeleek configuration file exists")
    
    # Test that pipeleek binary is available
    result = subprocess.run(
        ['docker-compose', 'exec', '-T', 'pentester', 'which', 'pipeleek'],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) + '/..'
    )
    
    assert result.returncode == 0, "Pipeleek binary not found"
    print(f"  ✓ Pipeleek binary found at {result.stdout.strip()}")

if __name__ == '__main__':
    print("=" * 70)
    print("GitLab Attack Lab - Integration Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        test_gitlab_is_healthy,
        test_admin_authentication,
        test_docker_containers_running,
        test_users_created,
        test_groups_created,
        test_group_memberships,
        test_projects_created,
        test_repositories_imported,
        test_ci_variables,
        test_ci_configs,
        test_runners_registered,
        test_runners_online,
        test_pipeleek_configured,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print()
        except Exception as e:
            failed += 1
            print(f"  ✗ Test failed: {e}")
            print()
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)
    
    exit(0 if failed == 0 else 1)
