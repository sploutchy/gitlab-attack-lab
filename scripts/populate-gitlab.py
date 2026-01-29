#!/usr/bin/env python3
"""
GitLab Lab Populator - Reads structure.yml and configures GitLab instance
"""

import sys
import os
import yaml
import requests
import time
from typing import Dict, List, Any, Optional

class GitLabPopulator:
    def __init__(self, gitlab_url: str, admin_token: str):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.admin_token = admin_token
        self.session = requests.Session()
        self.session.headers.update({'PRIVATE-TOKEN': admin_token})
        self.users_map = {}  # Map username to user ID
        self.groups_map = {}  # Map group path to group ID
        self.projects_map = {}  # Map project path to project ID
        
    def log(self, level: str, message: str):
        """Log message with level prefix"""
        print(f"[{level:>8}] {message}")
        
    def api_call(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API call to GitLab"""
        url = f"{self.gitlab_url}/api/v4/{endpoint}"
        try:
            if method == 'GET':
                resp = self.session.get(url)
            elif method == 'POST':
                resp = self.session.post(url, json=data)
            elif method == 'PUT':
                resp = self.session.put(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            resp.raise_for_status()
            return resp.json() if resp.text else None
        except requests.exceptions.RequestException as e:
            self.log("ERROR", f"API call failed: {e}")
            return None
    
    def wait_for_gitlab(self, max_attempts: int = 30) -> bool:
        """Wait for GitLab to be ready"""
        self.log("INFO", "Waiting for GitLab to be ready...")
        for attempt in range(max_attempts):
            try:
                resp = self.session.get(f"{self.gitlab_url}/api/v4/version")
                if resp.status_code in [200, 401]:
                    self.log("OK", "GitLab is ready!")
                    return True
            except:
                pass
            time.sleep(2)
        
        self.log("ERROR", "GitLab did not become ready in time")
        return False
    
    def create_user(self, user: Dict) -> Optional[int]:
        """Create a user in GitLab"""
        data = {
            'username': user['username'],
            'email': user['email'],
            'password': user['password'],
            'name': user.get('name', user['username']),
            'skip_confirmation': True
        }
        
        result = self.api_call('POST', 'users', data)
        if result:
            user_id = result['id']
            self.users_map[user['username']] = user_id
            self.log("OK", f"Created user: {user['username']} (ID: {user_id})")
            
            # Set admin status if needed
            if user.get('is_admin'):
                self.api_call('PUT', f'users/{user_id}', {'admin': True})
                self.log("OK", f"Set {user['username']} as admin")
            
            return user_id
        else:
            self.log("WARN", f"Failed to create user: {user['username']}")
            return None
    
    def create_group(self, group: Dict) -> Optional[int]:
        """Create a group in GitLab"""
        data = {
            'name': group['name'],
            'path': group['path'],
            'description': group.get('description', ''),
            'visibility': group.get('visibility', 'private')
        }
        
        result = self.api_call('POST', 'groups', data)
        if result:
            group_id = result['id']
            self.groups_map[group['path']] = group_id
            self.log("OK", f"Created group: {group['name']} (ID: {group_id})")
            
            # Add members
            for member in group.get('members', []):
                self._add_group_member(group_id, member)
            
            return group_id
        else:
            self.log("WARN", f"Failed to create group: {group['name']}")
            return None
    
    def _add_group_member(self, group_id: int, member: Dict):
        """Add a member to a group"""
        username = member['username']
        if username not in self.users_map:
            self.log("WARN", f"User {username} not found, skipping group membership")
            return
        
        user_id = self.users_map[username]
        data = {
            'user_id': user_id,
            'access_level': member.get('access_level', 30)
        }
        
        result = self.api_call('POST', f'groups/{group_id}/members', data)
        if result:
            self.log("OK", f"Added {username} to group {group_id}")
        else:
            self.log("WARN", f"Failed to add {username} to group")
    
    def create_project(self, project: Dict, parent_group: Optional[str] = None) -> Optional[int]:
        """Create a project in GitLab"""
        data = {
            'name': project['name'],
            'path': project['path'],
            'description': project.get('description', ''),
            'visibility': project.get('visibility', 'private'),
            'issues_enabled': project.get('issues_enabled', True),
            'wiki_enabled': project.get('wiki_enabled', False),
            'snippets_enabled': project.get('snippets_enabled', False),
            'builds_enabled': project.get('ci_cd_enabled', False),
        }
        
        # Add to group if specified
        if parent_group and parent_group in self.groups_map:
            data['namespace_id'] = self.groups_map[parent_group]
        
        result = self.api_call('POST', 'projects', data)
        if result:
            project_id = result['id']
            self.projects_map[project['path']] = project_id
            self.log("OK", f"Created project: {project['name']} (ID: {project_id})")
            
            # Add variables
            for var in project.get('variables', []):
                self._add_project_variable(project_id, var)
            
            return project_id
        else:
            self.log("WARN", f"Failed to create project: {project['name']}")
            return None
    
    def _add_project_variable(self, project_id: int, variable: Dict):
        """Add a CI/CD variable to a project"""
        data = {
            'key': variable['key'],
            'value': variable['value'],
            'protected': variable.get('protected', False),
            'masked': variable.get('masked', False)
        }
        
        result = self.api_call('POST', f'projects/{project_id}/variables', data)
        if result:
            self.log("OK", f"Added variable {variable['key']} to project {project_id}")
        else:
            self.log("WARN", f"Failed to add variable {variable['key']}")
    
    def populate_from_yaml(self, yaml_file: str) -> bool:
        """Load YAML file and populate GitLab"""
        try:
            with open(yaml_file, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            self.log("ERROR", f"Failed to load YAML: {e}")
            return False
        
        self.log("INFO", f"Loaded configuration: {config.get('lab', {}).get('name', 'Unknown')}")
        
        # Test if admin token works
        result = self.api_call('GET', 'version')
        if result is None:
            self.log("ERROR", "Admin token is invalid or GitLab API is not responding")
            self.log("ERROR", "Please ensure GITLAB_ADMIN_TOKEN in .env is valid")
            return False
        
        self.log("OK", f"Authenticated successfully with GitLab v{result.get('version', 'unknown')}")
        
        # Create users (skip root as it already exists)
        self.log("INFO", "Creating users...")
        for user in config.get('users', []):
            if user['username'] != 'root':  # Skip root user
                self.create_user(user)
            else:
                self.log("INFO", f"Skipping root user (already exists)")
                self.users_map['root'] = 1  # Root user is always ID 1
        
        # Create groups
        self.log("INFO", "Creating groups...")
        for group in config.get('groups', []):
            self.create_group(group)
        
        # Create projects
        self.log("INFO", "Creating projects...")
        for project in config.get('projects', []):
            group = project.get('group')
            self.create_project(project, group)
        
        self.log("OK", "Population complete!")
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 populate-gitlab.py <config.yml> [gitlab_url] [admin_token]")
        sys.exit(1)
    
    config_file = sys.argv[1]
    gitlab_url = sys.argv[2] if len(sys.argv) > 2 else os.getenv('GITLAB_URL', 'http://127.0.0.1')
    admin_token = sys.argv[3] if len(sys.argv) > 3 else os.getenv('GITLAB_ADMIN_TOKEN', 'glpat-attack-lab-admin-token-2024')
    
    populator = GitLabPopulator(gitlab_url, admin_token)
    
    # Wait for GitLab to be ready
    if not populator.wait_for_gitlab():
        sys.exit(1)
    
    # Populate from YAML
    if not populator.populate_from_yaml(config_file):
        sys.exit(1)
    
    print("\n✅ GitLab lab structure successfully populated!")
    sys.exit(0)


if __name__ == '__main__':
    main()
