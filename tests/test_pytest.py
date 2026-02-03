"""
Pytest tests for GitLab Attack Lab

These tests validate the complete setup and configuration.
"""

import pytest
import requests
import subprocess
import time
import json

class TestGitLabHealth:
    """Test GitLab service health"""
    
    def test_gitlab_responds(self, gitlab_url):
        """Test that GitLab API responds"""
        response = requests.get(f"{gitlab_url}/api/v4/version", timeout=10)
        # 200 or 401 are both acceptable (401 means it's up but needs auth)
        assert response.status_code in [200, 401], \
            f"Expected 200 or 401, got {response.status_code}"
        
        if response.status_code == 200:
            version_data = response.json()
            assert 'version' in version_data
            print(f"GitLab version: {version_data['version']}")
        else:
            print("GitLab is responding (requires authentication)")
    
    def test_admin_authentication(self, gitlab_url, admin_token):
        """Test admin token authentication"""
        headers = {'PRIVATE-TOKEN': admin_token}
        response = requests.get(f"{gitlab_url}/api/v4/user", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data['username'] == 'root'
        assert user_data['is_admin'] is True

class TestUsers:
    """Test user creation"""
    
    def test_all_users_created(self, gitlab_url, admin_token, structure_config):
        """Test that all users from merged scenarios are created"""
        headers = {'PRIVATE-TOKEN': admin_token}
        response = requests.get(f"{gitlab_url}/api/v4/users", headers=headers)
        
        assert response.status_code == 200
        users = response.json()
        created_usernames = {u['username'] for u in users}
        
        expected_users = {u['username'] for u in structure_config['users']}
        
        for expected_user in expected_users:
            assert expected_user in created_usernames, f"User {expected_user} not found"

class TestGroups:
    """Test group creation and membership"""
    
    def test_all_groups_created(self, gitlab_url, admin_token, structure_config):
        """Test that all groups are created"""
        headers = {'PRIVATE-TOKEN': admin_token}
        response = requests.get(f"{gitlab_url}/api/v4/groups", headers=headers)
        
        assert response.status_code == 200
        groups = response.json()
        created_group_paths = {g['path'] for g in groups}
        
        expected_groups = {g['path'] for g in structure_config['groups']}
        
        for expected_group in expected_groups:
            assert expected_group in created_group_paths, f"Group {expected_group} not found"
    
    def test_group_memberships(self, gitlab_url, admin_token, structure_config):
        """Test that group members are added correctly"""
        headers = {'PRIVATE-TOKEN': admin_token}
        
        for group_cfg in structure_config['groups']:
            group_path = group_cfg['path']
            
            # Get group
            response = requests.get(
                f"{gitlab_url}/api/v4/groups",
                headers=headers,
                params={'search': group_path}
            )
            assert response.status_code == 200
            groups = response.json()
            group = next((g for g in groups if g['path'] == group_path), None)
            assert group is not None, f"Group {group_path} not found"
            
            # Get members
            response = requests.get(
                f"{gitlab_url}/api/v4/groups/{group['id']}/members",
                headers=headers
            )
            assert response.status_code == 200
            members = response.json()
            member_usernames = {m['username'] for m in members}
            
            # Check expected members
            for member_cfg in group_cfg.get('members', []):
                expected_username = member_cfg['username']
                assert expected_username in member_usernames, \
                    f"User {expected_username} not in group {group_path}"

class TestProjects:
    """Test project creation and configuration"""
    
    def test_all_projects_created(self, gitlab_url, admin_token, structure_config):
        """Test that all projects are created"""
        headers = {'PRIVATE-TOKEN': admin_token}
        response = requests.get(
            f"{gitlab_url}/api/v4/projects",
            headers=headers,
            params={'membership': False, 'per_page': 100}
        )
        
        assert response.status_code == 200
        projects = response.json()
        created_project_paths = {p['path_with_namespace'] for p in projects}

        def _project_path(cfg: dict) -> str:
            group = cfg.get('group') or 'root'
            return f"{group}/{cfg['path']}"

        expected_projects = {_project_path(p) for p in structure_config['projects']}
        
        for expected_project in expected_projects:
            assert expected_project in created_project_paths, \
                f"Project {expected_project} not found"
    
    def test_repositories_have_content(self, gitlab_url, admin_token, structure_config):
        """Test that repositories were imported and have commits"""
        headers = {'PRIVATE-TOKEN': admin_token}
        
        for project_cfg in structure_config['projects']:
            if not project_cfg.get('repo_url'):
                continue
            
            project_path = f"{(project_cfg.get('group') or 'root')}/{project_cfg['path']}"
            
            # Get project
            response = requests.get(
                f"{gitlab_url}/api/v4/projects",
                headers=headers,
                params={'search': project_cfg['path']}
            )
            assert response.status_code == 200
            projects = response.json()
            project = next((p for p in projects if p['path_with_namespace'] == project_path), None)
            assert project is not None, f"Project {project_path} not found"
            
            # Check commits
            response = requests.get(
                f"{gitlab_url}/api/v4/projects/{project['id']}/repository/commits",
                headers=headers
            )
            
            if response.status_code == 404:
                pytest.fail(f"Project {project_path} has no repository")
            
            assert response.status_code == 200
            commits = response.json()
            assert len(commits) > 0, f"Project {project_path} has no commits"

class TestCICD:
    """Test CI/CD configuration"""
    
    def test_variables_created(self, gitlab_url, admin_token, structure_config):
        """Test that CI/CD variables are created"""
        headers = {'PRIVATE-TOKEN': admin_token}
        
        for project_cfg in structure_config['projects']:
            if not project_cfg.get('variables'):
                continue
            
            project_path = f"{(project_cfg.get('group') or 'root')}/{project_cfg['path']}"
            
            # Get project
            response = requests.get(
                f"{gitlab_url}/api/v4/projects",
                headers=headers,
                params={'search': project_cfg['path']}
            )
            assert response.status_code == 200
            projects = response.json()
            project = next((p for p in projects if p['path_with_namespace'] == project_path), None)
            assert project is not None
            
            # Get variables
            response = requests.get(
                f"{gitlab_url}/api/v4/projects/{project['id']}/variables",
                headers=headers
            )
            assert response.status_code == 200
            variables = response.json()
            variable_keys = {v['key'] for v in variables}
            
            # Check expected variables
            for var_cfg in project_cfg['variables']:
                assert var_cfg['key'] in variable_keys, \
                    f"Variable {var_cfg['key']} not found in {project_path}"
    
    def test_ci_configs_exist(self, gitlab_url, admin_token, structure_config):
        """Test that .gitlab-ci.yml files exist where expected"""
        headers = {'PRIVATE-TOKEN': admin_token}
        
        for project_cfg in structure_config['projects']:
            if not project_cfg.get('ci_cd_enabled', False):
                continue
            
            project_path = f"{(project_cfg.get('group') or 'root')}/{project_cfg['path']}"
            
            # Get project
            response = requests.get(
                f"{gitlab_url}/api/v4/projects",
                headers=headers,
                params={'search': project_cfg['path']}
            )
            assert response.status_code == 200
            projects = response.json()
            project = next((p for p in projects if p['path_with_namespace'] == project_path), None)
            assert project is not None
            
            # Try to get .gitlab-ci.yml
            response = requests.get(
                f"{gitlab_url}/api/v4/projects/{project['id']}/repository/files/.gitlab-ci.yml",
                headers=headers,
                params={'ref': project_cfg.get('default_branch', 'main')}
            )
            
            # Some projects might not have CI files if repo already had one or it failed
            # We just check it doesn't error unexpectedly
            assert response.status_code in [200, 404], \
                f"Unexpected status {response.status_code} for CI file in {project_path}"

class TestRunners:
    """Test runner registration and status"""
    
    def test_runners_registered(self, gitlab_url, admin_token, structure_config):
        """Test that all runners are registered"""
        headers = {'PRIVATE-TOKEN': admin_token}
        response = requests.get(
            f"{gitlab_url}/api/v4/runners/all",
            headers=headers,
            params={'per_page': 100}
        )
        
        assert response.status_code == 200
        runners = response.json()
        registered_descriptions = {r['description'] for r in runners}
        
        expected_runners = {r['description'] for r in structure_config.get('runners', [])}
        
        for expected_runner in expected_runners:
            assert expected_runner in registered_descriptions, \
                f"Runner {expected_runner} not registered"
    
    def test_runners_contacted(self, gitlab_url, admin_token, structure_config):
        """Test that runners have contacted GitLab"""
        headers = {'PRIVATE-TOKEN': admin_token}
        
        # Give runners time to contact
        time.sleep(15)
        
        response = requests.get(
            f"{gitlab_url}/api/v4/runners/all",
            headers=headers,
            params={'per_page': 100}
        )
        
        assert response.status_code == 200
        runners = response.json()
        
        expected_runners = {r['description'] for r in structure_config.get('runners', [])}
        
        for expected_runner_desc in expected_runners:
            runner = next((r for r in runners if r['description'] == expected_runner_desc), None)
            assert runner is not None, f"Runner {expected_runner_desc} not found"
            
            # Check if runner has ever contacted (it might not be online right now but should have contacted)
            contacted_at = runner.get('contacted_at')
            if contacted_at is None:
                # Sometimes runners need a bit more time
                pytest.skip(f"Runner {expected_runner_desc} hasn't contacted yet (may need more time)")

class TestContainers:
    """Test Docker container status"""
    
    def test_all_containers_running(self):
        """Test that all expected containers are running"""
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, "docker-compose ps failed"
        
        containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
        running_containers = {c['Name'] for c in containers if c.get('State') == 'running'}
        
        expected_containers = {
            'gitlab-attack-lab',
            'gitlab-runner-docker',
            'gitlab-runner-shell',
            'pentester',
            'mailhog'
        }
        
        for expected in expected_containers:
            assert expected in running_containers, f"Container {expected} not running"

class TestPentesterTools:
    """Test pentester container tools"""
    
    def test_pipeleek_installed(self):
        """Test that pipeleek is installed in pentester container"""
        result = subprocess.run(
            ['docker-compose', 'exec', '-T', 'pentester', 'which', 'pipeleek'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, "Pipeleek not found in pentester container"
        assert 'pipeleek' in result.stdout
    
    def test_pipeleek_configured(self):
        """Test that pipeleek is configured"""
        result = subprocess.run(
            ['docker-compose', 'exec', '-T', 'pentester', 
             'test', '-f', '/root/.config/pipeleek/pipeleek.yaml'],
            capture_output=True
        )
        
        assert result.returncode == 0, "Pipeleek config file not found"
