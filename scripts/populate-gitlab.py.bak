#!/usr/bin/env python3
"""
GitLab Lab Populator - Reads a merged YAML config and configures GitLab instance
"""

import sys
import os
import json
import yaml
import requests
import time
from urllib.parse import quote
from typing import Dict, List, Any, Optional

class GitLabPopulator:
    def __init__(self, gitlab_url: str, admin_token: str, config_base_path: str = None):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.admin_token = admin_token
        self.session = requests.Session()
        self.session.headers.update({'PRIVATE-TOKEN': admin_token})
        self.users_map = {}  # Map username to user ID
        self.groups_map = {}  # Map group path to group ID
        self.projects_map = {}  # Map project path to project ID
        self.user_tokens = {}  # Map "username:alias" to PAT token
        self.ci_templates = self._build_ci_templates()
        self.config_base_path = config_base_path or os.path.dirname(os.path.abspath(__file__))

    def _build_ci_templates(self) -> Dict[str, str]:
        """Build default CI templates for lab projects (deprecated - use external files)"""
        # Keep empty for backward compatibility but log warning if used
        return {}
    def _build_ci_templates(self) -> Dict[str, str]:
        """Build default CI templates for lab projects (deprecated - use external files)"""
        # Keep empty for backward compatibility but log warning if used
        return {}

    def _validate_ci_template(self, template_path: str) -> bool:
        """Validate that a CI template file exists and is readable"""
        full_path = os.path.join(self.config_base_path, template_path)
        
        if not os.path.exists(full_path):
            # Try absolute path
            full_path = template_path
        
        if not os.path.exists(full_path):
            return False
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
                if not content.strip():
                    return False
                # Basic YAML validation
                yaml.safe_load(content)
                return True
        except Exception as e:
            self.log("WARN", f"CI template validation failed for {template_path}: {e}")
            return False

    def _create_personal_access_token(self, user_id: int, username: str, token_name: str, token_alias: str, scopes: List[str] = None) -> Optional[str]:
        """Create a personal access token for a user (requires admin)"""
        if scopes is None:
            # Default scopes - use only those supported in GitLab v18.x
            # Removed: sudo, admin_mode (not available in this version)
            scopes = ["api", "read_user", "read_repository", "write_repository"]
        
        # Calculate expiration date (365 days from now)
        from datetime import datetime, timedelta
        expires_at = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        data = {
            'name': token_name,
            'scopes': scopes,
            'expires_at': expires_at
        }
        
        self.log("DEBUG", f"Creating PAT '{token_name}' for user {username} (ID: {user_id}) with scopes: {scopes}")
        self.log("DEBUG", f"Sending POST request to users/{user_id}/personal_access_tokens with data: {data}")
        
        result = self.api_call('POST', f'users/{user_id}/personal_access_tokens', data)
        
        if result:
            self.log("DEBUG", f"API response received: {result}")
            if 'token' in result:
                token = result['token']
                token_key = f"{username}:{token_alias}"
                self.user_tokens[token_key] = token
                self.log("OK", f"Created PAT '{token_name}' (alias: {token_alias}) for {username}, stored as {token_key}")
                return token
            else:
                self.log("ERROR", f"API response missing 'token' field for PAT creation: {result}")
                return None
        else:
            self.log("ERROR", f"Failed to create PAT '{token_name}' for {username} (API returned None)")
            return None

    def _load_ci_template_file(self, template_path: str) -> Optional[str]:
        # Try relative to config base path first
        full_path = os.path.join(self.config_base_path, template_path)
        
        if not os.path.exists(full_path):
            # Try absolute path
            full_path = template_path
        
        if not os.path.exists(full_path):
            self.log("WARN", f"CI template file not found: {template_path}")
            return None
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            self.log("INFO", f"Loaded CI template from {template_path}")
            return content
        except Exception as e:
            self.log("WARN", f"Failed to read CI template file {template_path}: {e}")
            return None
        
    def log(self, level: str, message: str):
        """Log message with level prefix"""
        print(f"[{level:>8}] {message}")
        
    def api_call(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None, suppress_errors: List[int] = None) -> Optional[Dict]:
        """Make API call to GitLab
        
        Args:
            suppress_errors: List of HTTP status codes to not log as errors (e.g., [404] for expected not-found)
        """
        url = f"{self.gitlab_url}/api/v4/{endpoint}"
        try:
            if method == 'GET':
                resp = self.session.get(url, params=params)
            elif method == 'POST':
                resp = self.session.post(url, json=data)
            elif method == 'PUT':
                resp = self.session.put(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            resp.raise_for_status()
            return resp.json() if resp.text else None
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            status_code = None
            try:
                if hasattr(e, 'response') and e.response:
                    status_code = e.response.status_code
                    resp_text = e.response.text
                    if resp_text:
                        # Try to parse as JSON for better error messages
                        try:
                            error_json = json.loads(resp_text)
                            if 'message' in error_json:
                                error_msg = f"{error_json['message']}"
                            elif 'error' in error_json:
                                error_msg = f"{error_json['error']}"
                            elif 'error_description' in error_json:
                                error_msg = f"{error_json['error_description']}"
                            else:
                                error_msg = resp_text[:300]
                        except:
                            error_msg = resp_text[:300]
                    # For 403, also log the request data that caused it
                    if status_code == 403:
                        error_msg += f" (payload: {str(data)[:100]}...)" if data else ""
            except:
                pass
            
            # Check if this error should be suppressed
            if suppress_errors and status_code in suppress_errors:
                return None
            
            # Format complete error message with status code (only log if not suppressed)
            if status_code:
                self.log("ERROR", f"API call failed [{status_code} {method} {endpoint}]: {error_msg}")
            else:
                self.log("ERROR", f"API call failed [{method} {endpoint}]: {error_msg}")
            return None

    def _resolve_branch(self, project_id: int, preferred_branch: Optional[str]) -> str:
        """Resolve a valid branch for operations, falling back to project default."""
        # Suppress 404 errors when checking branch existence (expected for empty repos)
        if preferred_branch:
            encoded_branch = quote(preferred_branch, safe="")
            branch_info = self.api_call('GET', f'projects/{project_id}/repository/branches/{encoded_branch}', suppress_errors=[404])
            if branch_info:
                return preferred_branch

        project_info = self.api_call('GET', f'projects/{project_id}')
        default_branch = project_info.get('default_branch') if project_info else None
        if default_branch:
            return default_branch

        for fallback in ('main', 'master'):
            encoded_branch = quote(fallback, safe="")
            branch_info = self.api_call('GET', f'projects/{project_id}/repository/branches/{encoded_branch}', suppress_errors=[404])
            if branch_info:
                return fallback

        return preferred_branch or 'main'

    def _wait_for_import(self, project_id: int, max_attempts: int = 60) -> bool:
        """Wait for repository import to finish"""
        for attempt in range(max_attempts):
            result = self.api_call('GET', f'projects/{project_id}')
            if not result:
                time.sleep(2)
                continue

            status = result.get('import_status')
            if status in (None, 'finished'):
                return True
            if status == 'failed':
                self.log("ERROR", f"Import failed for project {project_id}")
                return False

            if attempt % 5 == 0:
                self.log("INFO", f"Waiting for import of project {project_id} (status: {status})")
            time.sleep(2)

        self.log("ERROR", f"Import did not finish for project {project_id}")
        return False

    def _get_all_runners(self) -> List[Dict[str, Any]]:
        """Fetch all runners (admin token required)"""
        runners: List[Dict[str, Any]] = []
        page = 1
        while True:
            page_data = self.api_call('GET', 'runners/all', params={'per_page': 100, 'page': page})
            if not page_data:
                break
            runners.extend(page_data)
            if len(page_data) < 100:
                break
            page += 1
        return runners

    def _find_runner_by_description(self, runners: List[Dict[str, Any]], description: str) -> Optional[Dict[str, Any]]:
        """Find runner by description"""
        for runner in runners:
            if runner.get('description') == description:
                return runner
        return None

    def create_runner(self, runner_cfg: Dict[str, Any]) -> Optional[str]:
        """Create a runner and return its authentication token"""
        scope = runner_cfg.get('scope', 'instance')
        scope_target = runner_cfg.get('scope_target')
        
        # Determine runner type and group/project ID
        runner_type = 'instance_type'
        group_id = None
        project_id = None
        
        if scope == 'group' and scope_target:
            runner_type = 'group_type'
            group_id = self.groups_map.get(scope_target)
            if not group_id:
                self.log("ERROR", f"Group not found: {scope_target}")
                return None
        elif scope == 'project' and scope_target:
            runner_type = 'project_type'
            project_id = self.projects_map.get(scope_target)
            if not project_id:
                self.log("ERROR", f"Project not found: {scope_target}")
                return None
        
        data = {
            'runner_type': runner_type,
            'description': runner_cfg.get('description', 'runner'),
            'tag_list': runner_cfg.get('tags', []),
            'run_untagged': runner_cfg.get('run_untagged', True),
            'locked': runner_cfg.get('locked', False),
            'access_level': runner_cfg.get('access_level', 'not_protected'),
        }
        
        if group_id:
            data['group_id'] = group_id
        if project_id:
            data['project_id'] = project_id
        
        result = self.api_call('POST', 'user/runners', data)
        if result:
            token = result.get('token')
            scope_info = f" ({scope}" + (f": {scope_target}" if scope_target else "") + ")"
            self.log("OK", f"Created runner: {runner_cfg.get('description')}{scope_info} (token: {token[:12]}...)")
            return token
        else:
            self.log("ERROR", f"Failed to create runner: {runner_cfg.get('description')}")
            return None

    def create_runners(self, runners_config: List[Dict[str, Any]]) -> Dict[str, str]:
        """Create all runners and return mapping of description to token"""
        if not runners_config:
            return {}

        self.log("INFO", "Creating runners...")
        tokens = {}
        for runner_cfg in runners_config:
            description = runner_cfg.get('description')
            if not description:
                continue
            
            token = self.create_runner(runner_cfg)
            if token:
                tokens[description] = token
        
        return tokens

    def _create_file(self, project_id: int, file_path: str, content: str, branch: str, commit_message: str) -> bool:
        """Create or update a file in the repository with retry logic"""
        resolved_branch = self._resolve_branch(project_id, branch)
        encoded_path = quote(file_path, safe="")
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # First check if file exists (suppress 404 - expected if file doesn't exist yet)
                existing = self.api_call('GET', f'projects/{project_id}/repository/files/{encoded_path}', params={'ref': resolved_branch}, suppress_errors=[404])
                
                if existing:
                    # File exists, update it - must include last_commit_id
                    data = {
                        'branch': resolved_branch,
                        'content': content,
                        'commit_message': commit_message,
                        'last_commit_id': existing.get('last_commit_id') or existing.get('commit_id')
                    }
                    result = self.api_call('PUT', f'projects/{project_id}/repository/files/{encoded_path}', data)
                    if result:
                        self.log("OK", f"Updated {file_path} in project {project_id}")
                        return True
                else:
                    # File doesn't exist, create it
                    data = {
                        'branch': resolved_branch,
                        'content': content,
                        'commit_message': commit_message
                    }
                    result = self.api_call('POST', f'projects/{project_id}/repository/files/{encoded_path}', data)
                    if result:
                        self.log("OK", f"Created {file_path} in project {project_id}")
                        return True
                
                # If we get here, the API call returned None (error)
                # For first two attempts, wait and retry
                if attempt < max_attempts - 1:
                    self.log("INFO", f"File creation failed for project {project_id}, retrying in 3 seconds... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(3)
                
            except Exception as e:
                self.log("INFO", f"File creation error for project {project_id}: {str(e)}, retrying... (attempt {attempt + 1}/{max_attempts})")
                if attempt < max_attempts - 1:
                    time.sleep(3)

        self.log("WARN", f"Failed to create/update {file_path} in project {project_id} after {max_attempts} attempts")
        return False

    def _ensure_ci_config(self, project_id: int, project_path: str, default_branch: Optional[str]):
        """Ensure a .gitlab-ci.yml exists in the project"""
        template = self.ci_templates.get(project_path)
        if not template:
            self.log("INFO", f"No CI template for project {project_path}, skipping")
            return

        resolved_branch = self._resolve_branch(project_id, default_branch)

        self._create_file(
            project_id=project_id,
            file_path='.gitlab-ci.yml',
            content=template,
            branch=resolved_branch,
            commit_message='Add default GitLab CI pipeline'
        )
    
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
        # Check if user already exists
        existing = self.api_call('GET', f'users?username={user["username"]}')
        if existing and len(existing) > 0:
            user_id = existing[0]['id']
            self.users_map[user['username']] = user_id
            self.log("OK", f"User already exists: {user['username']} (ID: {user_id})")
            # Still process PATs even if user already exists (idempotent re-runs)
            if 'personal_access_tokens' in user:
                for pat_config in user['personal_access_tokens']:
                    self._create_personal_access_token(
                        user_id=user_id,
                        username=user['username'],
                        token_name=pat_config.get('name', 'automation-token'),
                        token_alias=pat_config.get('alias', 'default'),
                        scopes=pat_config.get('scopes')
                    )
            return user_id
        
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
            
            # Generate PATs if configured
            if 'personal_access_tokens' in user:
                for pat_config in user['personal_access_tokens']:
                    self._create_personal_access_token(
                        user_id=user_id,
                        username=user['username'],
                        token_name=pat_config.get('name', 'automation-token'),
                        token_alias=pat_config.get('alias', 'default'),
                        scopes=pat_config.get('scopes')
                    )
            
            return user_id
        else:
            self.log("WARN", f"Failed to create user: {user['username']}")
            return None
    
    def create_group(self, group: Dict) -> Optional[int]:
        """Create a group in GitLab"""
        # Check if group already exists
        existing = self.api_call('GET', f'groups?search={group["path"]}')
        if existing and len(existing) > 0:
            for g in existing:
                if g.get('path') == group['path']:
                    group_id = g['id']
                    self.groups_map[group['path']] = group_id
                    self.log("OK", f"Group already exists: {group['name']} (ID: {group_id})")
                    # Still add members
                    for member in group.get('members', []):
                        self._add_group_member(group_id, member)
                    return group_id
        
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
        
        result = self.api_call('POST', f'groups/{group_id}/members', data, suppress_errors=[409])
        if result:
            self.log("OK", f"Added {username} to group {group_id}")
        else:
            # 409 Conflict is expected on idempotent re-runs (member already exists)
            # Don't log a warning in this case
            pass
    
    def _add_project_member(self, project_id: int, member: Dict):
        """Add a member to a project"""
        username = member['username']
        if username not in self.users_map:
            self.log("WARN", f"User {username} not found, skipping project membership")
            return
        
        user_id = self.users_map[username]
        data = {
            'user_id': user_id,
            'access_level': member.get('access_level', 30)
        }
        
        result = self.api_call('POST', f'projects/{project_id}/members', data, suppress_errors=[409])
        if result:
            self.log("OK", f"Added {username} to project {project_id}")
        else:
            # 409 Conflict is expected on idempotent re-runs (member already exists)
            # Don't log a warning in this case
            pass
    
    def create_project(self, project: Dict, parent_group: Optional[str] = None) -> Optional[int]:
        """Create a project in GitLab (idempotent - checks if exists first)"""
        # Check if project already exists (idempotent re-runs)
        search_path = project['path']
        existing = self.api_call('GET', f'projects?search={search_path}')
        if existing and len(existing) > 0:
            for p in existing:
                if p.get('path') == search_path:
                    project_id = p['id']
                    self.projects_map[project['path']] = project_id
                    self.log("OK", f"Project already exists: {project['name']} (ID: {project_id})")
                    
                    # Still add members (may be new, expect 409 Conflict on re-runs)
                    for member in project.get('members', []):
                        self._add_project_member(project_id, member)
                    
                    # Still add/update variables (may be new, expect 404 on re-runs)
                    for var in project.get('variables', []):
                        self._add_project_variable(project_id, var)
                    
                    # Still ensure CI config file exists (may be new)
                    ci_cd_template_path = project.get('ci_cd_template')
                    
                    if ci_cd_template_path:
                        # Validate template exists
                        if not self._validate_ci_template(ci_cd_template_path):
                            self.log("ERROR", f"CI template not found or invalid: {ci_cd_template_path}")
                        else:
                            # Load CI from template file
                            template_content = self._load_ci_template_file(ci_cd_template_path)
                            if template_content:
                                resolved_branch = self._resolve_branch(project_id, project.get('default_branch', 'main'))
                                self._create_file(
                                    project_id=project_id,
                                    file_path='.gitlab-ci.yml',
                                    content=template_content,
                                    branch=resolved_branch,
                                    commit_message='Add GitLab CI pipeline configuration'
                                )
                    elif project.get('ci_cd_enabled'):
                        self.log("WARN", f"Project {project['name']} has ci_cd_enabled but no ci_cd_template specified")
                    
                    # Still add schedules if needed
                    for schedule in project.get('schedules', []):
                        self._add_project_schedule(project_id, schedule)
                    
                    return project_id
        
        repo_url = project.get('repo_url')
        data = {
            'name': project['name'],
            'path': project['path'],
            'description': project.get('description', ''),
            'visibility': project.get('visibility', 'private'),
            'issues_enabled': project.get('issues_enabled', True),
            'merge_requests_enabled': project.get('merge_requests_enabled', True),
            'wiki_enabled': project.get('wiki_enabled', False),
            'snippets_enabled': project.get('snippets_enabled', False),
            'builds_enabled': project.get('ci_cd_enabled', False),
            'initialize_with_readme': not repo_url,  # Only init README if no import
            'default_branch': project.get('default_branch', 'main')
        }
        
        # Add to group if specified and group exists
        if parent_group:
            if parent_group in self.groups_map:
                data['namespace_id'] = self.groups_map[parent_group]
            else:
                self.log("WARN", f"Group not found: {parent_group}, creating project in user namespace")
        
        result = self.api_call('POST', 'projects', data)
        if result:
            project_id = result['id']
            project_path_with_namespace = result['path_with_namespace']
            self.projects_map[project['path']] = project_id
            self.log("OK", f"Created project: {project['name']} (ID: {project_id})")
            
            # Import repository if URL specified
            if repo_url:
                self._import_via_git_clone(project_id, project_path_with_namespace, repo_url)

            # Add members
            for member in project.get('members', []):
                self._add_project_member(project_id, member)

            # Add variables
            for var in project.get('variables', []):
                self._add_project_variable(project_id, var)

            # Create CI config file (template only - no inline support)
            ci_cd_template_path = project.get('ci_cd_template')
            
            if ci_cd_template_path:
                # Validate template exists
                if not self._validate_ci_template(ci_cd_template_path):
                    self.log("ERROR", f"CI template not found or invalid: {ci_cd_template_path}")
                else:
                    # Load CI from template file
                    template_content = self._load_ci_template_file(ci_cd_template_path)
                    if template_content:
                        self._create_file(
                            project_id=project_id,
                            file_path='.gitlab-ci.yml',
                            content=template_content,
                            branch=project.get('default_branch', 'main'),
                            commit_message='Add GitLab CI pipeline configuration'
                        )
            elif project.get('ci_cd_enabled'):
                self.log("WARN", f"Project {project['name']} has ci_cd_enabled but no ci_cd_template specified")

            # Add pipeline schedules (must be after CI file creation)
            for schedule in project.get('schedules', []):
                self._add_project_schedule(project_id, schedule)
            
            return project_id
        else:
            self.log("WARN", f"Failed to create project: {project['name']} (payload: name={project.get('name')}, path={project.get('path')}, visibility={project.get('visibility')})")
            return None
    
    def _import_via_git_clone(self, project_id: int, project_path: str, repo_url: str):
        """Import repository by cloning and pushing"""
        import subprocess
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            self.log("INFO", f"Cloning {repo_url}...")
            
            # Clone the source repository
            subprocess.run(
                ['git', 'clone', '--bare', repo_url, temp_dir],
                check=True,
                capture_output=True,
                timeout=120
            )
            
            # Get project URL with token - use gitlab_url (http://127.0.0.1) not hostname
            # Remove trailing slash if present
            base_url = self.gitlab_url.rstrip('/')
            gitlab_repo_url = f"http://oauth2:{self.admin_token}@{base_url.replace('http://', '')}/{project_path}.git"
            
            # Push to GitLab
            self.log("INFO", f"Pushing to GitLab project {project_path}...")
            subprocess.run(
                ['git', 'push', '--mirror', gitlab_repo_url],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                timeout=120
            )
            
            self.log("OK", f"Repository imported successfully for project {project_id}")
            
        except subprocess.TimeoutExpired:
            self.log("ERROR", f"Import timeout for project {project_id}")
        except subprocess.CalledProcessError as e:
            self.log("ERROR", f"Import failed for project {project_id}: {e.stderr.decode() if e.stderr else str(e)}")
        except Exception as e:
            self.log("ERROR", f"Import error for project {project_id}: {str(e)}")
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def _import_repository(self, project_id: int, repo_url: str):
        """Import a repository into an existing project"""
        # Use the remote mirror import endpoint
        data = {
            'url': repo_url,
            'import_type': 'git'
        }
        
        # Try the import via remote mirror
        import_data = {'url': repo_url}
        result = self.api_call('POST', f'projects/{project_id}/remote_mirrors', import_data)
        
        if not result:
            # Fallback: Try creating a push to import
            self.log("INFO", f"Remote mirror not available, project {project_id} will remain empty")
            return
            
        self.log("OK", f"Repository mirror set up for project {project_id}")
    
    def _add_project_variable(self, project_id: int, variable: Dict):
        """Add a CI/CD variable to a project"""
        # Resolve PAT placeholders like ${USER_PAT:username:alias}
        value = variable['value']
        
        # Check for PAT placeholder pattern
        import re
        pat_pattern = r'\$\{USER_PAT:([^:]+):([^}]+)\}'
        match = re.search(pat_pattern, value)
        if match:
            username = match.group(1)
            alias = match.group(2)
            token_key = f"{username}:{alias}"
            
            if token_key in self.user_tokens:
                value = self.user_tokens[token_key]
                self.log("INFO", f"Resolved PAT placeholder for {username}:{alias}")
            else:
                self.log("WARN", f"PAT not found for {username}:{alias}, using placeholder value")
        
        # Masked variables must be at least 8 characters long
        is_masked = variable.get('masked', False)
        
        if is_masked and len(value) < 8:
            self.log("WARN", f"Variable {variable['key']} cannot be masked (value too short, minimum 8 characters)")
            is_masked = False
        
        data = {
            'key': variable['key'],
            'value': value,
            'protected': variable.get('protected', False),
            'masked': is_masked
        }
        # Check if variable already exists (idempotent re-runs)
        # Suppress 404 errors since they're expected when variable doesn't exist yet
        encoded_key = quote(variable['key'], safe="")
        existing = self.api_call('GET', f'projects/{project_id}/variables/{encoded_key}', suppress_errors=[404])
        if existing:
            update_data = {
                'value': value,
                'protected': variable.get('protected', False),
                'masked': is_masked
            }
            result = self.api_call('PUT', f'projects/{project_id}/variables/{encoded_key}', update_data)
            if result:
                self.log("OK", f"Updated variable {variable['key']} in project {project_id}")
            else:
                self.log("WARN", f"Failed to update variable {variable['key']}")
            return

        result = self.api_call('POST', f'projects/{project_id}/variables', data)
        if result:
            self.log("OK", f"Added variable {variable['key']} to project {project_id}")
        else:
            self.log("WARN", f"Failed to add variable {variable['key']}")
    
    def _add_project_schedule(self, project_id: int, schedule: Dict):
        """Add a pipeline schedule to a project"""
        resolved_ref = self._resolve_branch(project_id, schedule.get('ref', 'main'))
        data = {
            'description': schedule.get('description', 'Pipeline schedule'),
            'cron': schedule.get('cron', '0 0 * * *'),
            'cron_timezone': schedule.get('cron_timezone', 'UTC'),
            'ref': resolved_ref,
            'active': schedule.get('active', True)
        }
        
        # Retry logic: schedules may fail if project isn't fully initialized yet
        max_attempts = 3
        for attempt in range(max_attempts):
            result = self.api_call('POST', f'projects/{project_id}/pipeline_schedules', data, suppress_errors=[400])
            if result:
                self.log("OK", f"Added schedule '{schedule.get('description')}' to project {project_id}")
                return True
            
            if attempt < max_attempts - 1:
                self.log("INFO", f"Schedule creation failed for project {project_id}, retrying in 2 seconds... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
            else:
                # 400 Bad Request is expected on re-runs when schedule already exists
                self.log("WARN", f"Failed to add schedule to project {project_id} after {max_attempts} attempts")
        
        return False


    
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
        
        # Check if current user is admin
        user_result = self.api_call('GET', 'user')
        if user_result:
            is_admin = user_result.get('is_admin', False)
            username = user_result.get('username', 'unknown')
            self.log("OK", f"Authenticated as {username} (admin: {is_admin})")
            if not is_admin:
                self.log("WARN", "Token user is not an admin - some operations may fail")
        
        self.log("OK", f"Connected to GitLab v{result.get('version', 'unknown')}")

        
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

        # Create runners and return tokens
        runner_tokens = self.create_runners(config.get('runners', []))
        
        self.log("OK", "Population complete!")
        return runner_tokens


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 populate-gitlab.py <merged-config.yml> [gitlab_url] [admin_token]")
        sys.exit(1)
    
    config_file = sys.argv[1]
    gitlab_url = sys.argv[2] if len(sys.argv) > 2 else os.getenv('GITLAB_URL', 'http://127.0.0.1')
    admin_token = sys.argv[3] if len(sys.argv) > 3 else os.getenv('GITLAB_ADMIN_TOKEN', 'glpat-attack-lab-admin-token-2024')
    
    # Get config base path - use lab-config directory as the base
    # This assumes scripts are in <root>/scripts and lab-config is in <root>/lab-config
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_base_path = os.path.join(project_root, 'lab-config')
    
    populator = GitLabPopulator(gitlab_url, admin_token, config_base_path)
    
    # Wait for GitLab to be ready
    if not populator.wait_for_gitlab():
        sys.exit(1)
    
    # Populate from YAML
    runner_tokens = populator.populate_from_yaml(config_file)
    if not runner_tokens:
        sys.exit(1)
    
    # Output runner tokens for setup script to capture
    print("\n=== RUNNER_TOKENS ===")
    for description, token in runner_tokens.items():
        print(f"{description}={token}")
    print("=== END_RUNNER_TOKENS ===")
    
    print("\n✅ GitLab lab structure successfully populated!")
    sys.exit(0)


if __name__ == '__main__':
    main()
