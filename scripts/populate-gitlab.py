#!/usr/bin/env python3
"""
GitLab Lab Populator - Reads a merged YAML config and configures GitLab instance
Uses the official python-gitlab SDK for all API interactions
"""

import sys
import os
import yaml
import time
import re
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import quote

import gitlab
from gitlab.exceptions import GitlabGetError, GitlabCreateError, GitlabUpdateError, GitlabError


class GitLabPopulator:
    def __init__(self, gitlab_url: str, admin_token: str, config_base_path: str = None):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.admin_token = admin_token
        warnings.filterwarnings(
            "ignore",
            message=r"The base URL in the server response differs from the user-provided base URL.*",
        )
        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=admin_token)
        self.users_map = {}  # Map username to user ID
        self.groups_map = {}  # Map group path to group ID
        self.projects_map = {}  # Map project path to project ID
        self.user_tokens = {}  # Map "username:alias" to PAT token
        self.config_base_path = config_base_path or os.path.dirname(os.path.abspath(__file__))

    def log(self, level: str, message: str):
        """Log message with level prefix"""
        print(f"[{level:>8}] {message}")

    def _validate_ci_template(self, template_path: str) -> bool:
        """Validate that a CI template file exists and is readable"""
        full_path = os.path.join(self.config_base_path, template_path)
        
        if not os.path.exists(full_path):
            full_path = template_path
        
        if not os.path.exists(full_path):
            return False
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
                if not content.strip():
                    return False
                yaml.safe_load(content)
                return True
        except Exception as e:
            self.log("WARN", f"CI template validation failed for {template_path}: {e}")
            return False

    def _load_ci_template_file(self, template_path: str) -> Optional[str]:
        """Load CI template content from file"""
        full_path = os.path.join(self.config_base_path, template_path)
        
        if not os.path.exists(full_path):
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

    def _create_personal_access_token(
        self, 
        user_id: int, 
        username: str, 
        token_name: str, 
        token_alias: str, 
        scopes: List[str] = None
    ) -> Optional[str]:
        """Create a personal access token for a user (requires admin)"""
        if scopes is None:
            scopes = ["api", "read_user", "read_repository", "write_repository"]
        
        expires_at = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        try:
            user = self.gl.users.get(user_id)
            token_data = {
                'name': token_name,
                'scopes': scopes,
                'expires_at': expires_at
            }
            result = user.personal_access_tokens.create(token_data)
            
            token = result.token
            token_key = f"{username}:{token_alias}"
            self.user_tokens[token_key] = token
            self.log("OK", f"Created PAT '{token_name}' (alias: {token_alias}) for {username}, stored as {token_key}")
            return token
        except Exception as e:
            self.log("ERROR", f"Failed to create PAT '{token_name}' for {username}: {e}")
            return None

    def _resolve_branch(self, project_id: int, preferred_branch: Optional[str]) -> str:
        """Resolve a valid branch for operations, falling back to project default"""
        try:
            project = self.gl.projects.get(project_id)
            
            if preferred_branch:
                try:
                    project.branches.get(preferred_branch)
                    return preferred_branch
                except GitlabGetError:
                    pass
            
            if project.default_branch:
                return project.default_branch
            
            for fallback in ('main', 'master'):
                try:
                    project.branches.get(fallback)
                    return fallback
                except GitlabGetError:
                    continue
            
            return preferred_branch or 'main'
        except Exception as e:
            self.log("WARN", f"Error resolving branch for project {project_id}: {e}")
            return preferred_branch or 'main'

    def _wait_for_import(self, project_id: int, max_attempts: int = 60) -> bool:
        """Wait for repository import to finish"""
        for attempt in range(max_attempts):
            try:
                project = self.gl.projects.get(project_id)
                status = project.import_status
                
                if status in (None, 'finished'):
                    return True
                if status == 'failed':
                    self.log("ERROR", f"Import failed for project {project_id}")
                    return False
                
                if attempt % 5 == 0:
                    self.log("INFO", f"Waiting for import of project {project_id} (status: {status})")
                time.sleep(2)
            except Exception as e:
                self.log("WARN", f"Error checking import status: {e}")
                time.sleep(2)
        
        self.log("ERROR", f"Import did not finish for project {project_id}")
        return False

    def _get_all_runners(self) -> List:
        """Fetch all runners (admin token required)"""
        try:
            return self.gl.runners.list(all=True)
        except Exception as e:
            self.log("WARN", f"Error fetching runners: {e}")
            return []

    def _find_runners_by_description(self, runners: List, description: str) -> List[Any]:
        """Find runners by description"""
        return [runner for runner in runners if runner.description == description]

    def create_runner(self, runner_cfg: Dict[str, Any]) -> Optional[str]:
        """Create a runner and return its authentication token"""
        scope = runner_cfg.get('scope', 'instance')
        scope_target = runner_cfg.get('scope_target')
        
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
            'active': runner_cfg.get('active', True)
        }
        
        if group_id:
            data['group_id'] = group_id
        elif project_id:
            data['project_id'] = project_id
        
        try:
            all_runners = self._get_all_runners()
            existing_runners = self._find_runners_by_description(all_runners, data['description'])
            
            if existing_runners:
                for runner in existing_runners:
                    try:
                        self.gl.runners.get(runner.id).delete()
                        self.log("INFO", f"Removed existing runner: {data['description']} (ID: {runner.id})")
                    except Exception as e:
                        self.log("WARN", f"Failed to remove runner {runner.id}: {e}")
            
            result = self.gl.user.runners.create(data)
            token = result.token
            self.log("OK", f"Created runner: {data['description']} (ID: {result.id})")
            return token
        except Exception as e:
            self.log("ERROR", f"Failed to create runner {data['description']}: {e}")
            return None

    def create_runners(self, runners_config: List[Dict[str, Any]]) -> Dict[str, str]:
        """Create all runners and return mapping of description to token"""
        runner_tokens = {}
        
        if not runners_config:
            self.log("INFO", "No runners to create")
            return runner_tokens
        
        self.log("INFO", "Creating runners...")
        for runner_cfg in runners_config:
            token = self.create_runner(runner_cfg)
            if token:
                runner_tokens[runner_cfg.get('description', 'runner')] = token
        
        return runner_tokens

    def _create_file(
        self, 
        project_id: int, 
        file_path: str, 
        content: str, 
        branch: str, 
        commit_message: str
    ) -> bool:
        """Create or update a file in the repository"""
        try:
            project = self.gl.projects.get(project_id)
            resolved_branch = self._resolve_branch(project_id, branch)
            
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Try to get existing file
                    f = project.files.get(file_path=file_path, ref=resolved_branch)
                    # File exists, update it
                    f.content = content
                    f.save(branch=resolved_branch, commit_message=commit_message)
                    self.log("OK", f"Updated {file_path} in project {project_id}")
                    return True
                except GitlabGetError:
                    # File doesn't exist, create it
                    data = {
                        'file_path': file_path,
                        'branch': resolved_branch,
                        'content': content,
                        'commit_message': commit_message
                    }
                    project.files.create(data)
                    self.log("OK", f"Created {file_path} in project {project_id}")
                    return True
                except Exception as e:
                    if attempt < max_attempts - 1:
                        self.log("INFO", f"Retry {attempt + 1}/{max_attempts} for {file_path} in project {project_id}")
                        time.sleep(2)
                    else:
                        raise
            
            return False
        except Exception as e:
            self.log("ERROR", f"Failed to create/update {file_path} in project {project_id}: {e}")
            return False

    def wait_for_gitlab(self, max_attempts: int = 30) -> bool:
        """Wait for GitLab to be ready"""
        for attempt in range(max_attempts):
            try:
                version = self.gl.version()
                self.log("OK", f"GitLab is ready (version: {version})")
                return True
            except Exception as e:
                if attempt % 5 == 0:
                    self.log("INFO", f"Waiting for GitLab... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
        
        self.log("ERROR", "GitLab did not become ready in time")
        return False

    def create_user(self, user: Dict) -> Optional[int]:
        """Create a user in GitLab"""
        try:
            # Check if user exists
            users = self.gl.users.list(username=user['username'])
            if users:
                user_id = users[0].id
                self.users_map[user['username']] = user_id
                self.log("OK", f"User already exists: {user['username']} (ID: {user_id})")
                
                # Still generate PATs if configured
                if 'personal_access_tokens' in user:
                    for pat_config in user['personal_access_tokens']:
                        self._create_personal_access_token(
                            user_id=user_id,
                            username=user['username'],
                            token_name=pat_config['name'],
                            token_alias=pat_config.get('alias', pat_config['name']),
                            scopes=pat_config.get('scopes')
                        )
                return user_id
            
            # Create new user
            data = {
                'username': user['username'],
                'email': user['email'],
                'password': user['password'],
                'name': user.get('name', user['username']),
                'skip_confirmation': True
            }
            
            result = self.gl.users.create(data)
            user_id = result.id
            self.users_map[user['username']] = user_id
            self.log("OK", f"Created user: {user['username']} (ID: {user_id})")
            
            # Set admin status if needed
            if user.get('is_admin'):
                result.admin = True
                result.save()
                self.log("OK", f"Set {user['username']} as admin")
            
            # Generate PATs if configured
            if 'personal_access_tokens' in user:
                for pat_config in user['personal_access_tokens']:
                    self._create_personal_access_token(
                        user_id=user_id,
                        username=user['username'],
                        token_name=pat_config['name'],
                        token_alias=pat_config.get('alias', pat_config['name']),
                        scopes=pat_config.get('scopes')
                    )
            
            return user_id
        except Exception as e:
            self.log("ERROR", f"Failed to create user {user['username']}: {e}")
            return None

    def create_group(self, group: Dict) -> Optional[int]:
        """Create a group in GitLab"""
        try:
            # Check if group exists
            groups = self.gl.groups.list(search=group['path'])
            for g in groups:
                if g.path == group['path']:
                    group_id = g.id
                    self.groups_map[group['path']] = group_id
                    self.log("OK", f"Group already exists: {group['name']} (ID: {group_id})")
                    
                    # Still add members
                    for member in group.get('members', []):
                        self._add_group_member(group_id, member)
                    return group_id
            
            # Create new group
            data = {
                'name': group['name'],
                'path': group['path'],
                'description': group.get('description', ''),
                'visibility': group.get('visibility', 'private')
            }
            
            result = self.gl.groups.create(data)
            group_id = result.id
            self.groups_map[group['path']] = group_id
            self.log("OK", f"Created group: {group['name']} (ID: {group_id})")
            
            # Add members
            for member in group.get('members', []):
                self._add_group_member(group_id, member)
            
            return group_id
        except Exception as e:
            self.log("ERROR", f"Failed to create group {group['name']}: {e}")
            return None

    def _add_group_member(self, group_id: int, member: Dict):
        """Add a member to a group"""
        username = member['username']
        if username not in self.users_map:
            self.log("WARN", f"User {username} not found, skipping group membership")
            return
        
        user_id = self.users_map[username]
        access_level = member.get('access_level', 30)
        
        try:
            group = self.gl.groups.get(group_id)
            group.members.create({'user_id': user_id, 'access_level': access_level})
            self.log("OK", f"Added {username} to group {group_id}")
        except GitlabCreateError as e:
            # 409 Conflict is expected on idempotent re-runs (member already exists)
            if "already exists" in str(e).lower() or "409" in str(e):
                pass  # Silent - this is expected on re-runs
            else:
                self.log("WARN", f"Failed to add {username} to group {group_id}: {e}")
        except Exception as e:
            self.log("WARN", f"Failed to add {username} to group {group_id}: {e}")

    def _add_project_member(self, project_id: int, member: Dict):
        """Add a member to a project"""
        username = member['username']
        if username not in self.users_map:
            self.log("WARN", f"User {username} not found, skipping project membership")
            return
        
        user_id = self.users_map[username]
        access_level = member.get('access_level', 30)
        
        try:
            project = self.gl.projects.get(project_id)
            project.members.create({'user_id': user_id, 'access_level': access_level})
            self.log("OK", f"Added {username} to project {project_id}")
        except GitlabCreateError as e:
            # 409 Conflict is expected on idempotent re-runs (member already exists)
            if "already exists" in str(e).lower() or "409" in str(e):
                pass  # Silent - this is expected on re-runs
            else:
                self.log("WARN", f"Failed to add {username} to project {project_id}: {e}")
        except Exception as e:
            self.log("WARN", f"Failed to add {username} to project {project_id}: {e}")

    def create_project(self, project: Dict, parent_group: Optional[str] = None) -> Optional[int]:
        """Create a project in GitLab (idempotent - checks if exists first)"""
        try:
            # Check if project already exists
            search_path = project['path']
            projects = self.gl.projects.list(search=search_path)
            
            for p in projects:
                if p.path == search_path:
                    project_id = p.id
                    self.projects_map[project['path']] = project_id
                    self.log("OK", f"Project already exists: {project['name']} (ID: {project_id})")
                    
                    # Still add members (may be new, conflict on re-runs is OK)
                    for member in project.get('members', []):
                        self._add_project_member(project_id, member)
                    
                    # Still add/update variables
                    for var in project.get('variables', []):
                        self._add_project_variable(project_id, var)
                    
                    # Still ensure CI config file exists
                    ci_cd_template_path = project.get('ci_cd_template')
                    if ci_cd_template_path:
                        if not self._validate_ci_template(ci_cd_template_path):
                            self.log("ERROR", f"CI template not found or invalid: {ci_cd_template_path}")
                        else:
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
            
            # Create new project
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
                'jobs_enabled': project.get('ci_cd_enabled', False),
                'initialize_with_readme': not repo_url,
                'default_branch': project.get('default_branch', 'main')
            }
            
            # Add to group if specified
            if parent_group and parent_group in self.groups_map:
                data['namespace_id'] = self.groups_map[parent_group]
            elif parent_group:
                self.log("WARN", f"Group not found: {parent_group}, creating project in user namespace")
            
            result = self.gl.projects.create(data)
            project_id = result.id
            project_path_with_namespace = result.path_with_namespace
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
            
            # Create CI config file
            ci_cd_template_path = project.get('ci_cd_template')
            if ci_cd_template_path:
                if not self._validate_ci_template(ci_cd_template_path):
                    self.log("ERROR", f"CI template not found or invalid: {ci_cd_template_path}")
                else:
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
            
            # Add schedules
            for schedule in project.get('schedules', []):
                self._add_project_schedule(project_id, schedule)
            
            return project_id
        except Exception as e:
            self.log("ERROR", f"Failed to create project {project['name']}: {e}")
            return None

    def _import_via_git_clone(self, project_id: int, project_path: str, repo_url: str):
        """Import repository by cloning and pushing"""
        import subprocess
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            self.log("INFO", f"Cloning {repo_url}...")
            
            subprocess.run(
                ['git', 'clone', '--bare', repo_url, temp_dir],
                check=True,
                capture_output=True,
                timeout=120
            )
            
            base_url = self.gitlab_url.rstrip('/')
            gitlab_repo_url = f"http://oauth2:{self.admin_token}@{base_url.replace('http://', '')}/{project_path}.git"
            
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
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    def _add_project_variable(self, project_id: int, variable: Dict):
        """Add a CI/CD variable to a project"""
        try:
            # Resolve PAT placeholders
            value = variable['value']
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
            
            # Validate masked variables
            is_masked = variable.get('masked', False)
            if is_masked and len(value) < 8:
                self.log("WARN", f"Variable {variable['key']} cannot be masked (value too short)")
                is_masked = False
            
            data = {
                'key': variable['key'],
                'value': value,
                'protected': variable.get('protected', False),
                'masked': is_masked
            }
            
            project = self.gl.projects.get(project_id)
            
            # Check if variable exists
            try:
                var = project.variables.get(variable['key'])
                # Update existing variable
                var.value = value
                var.protected = data['protected']
                var.masked = is_masked
                var.save()
                self.log("OK", f"Updated variable {variable['key']} in project {project_id}")
            except GitlabGetError:
                # Create new variable
                project.variables.create(data)
                self.log("OK", f"Added variable {variable['key']} to project {project_id}")
        except Exception as e:
            self.log("WARN", f"Failed to add/update variable {variable['key']}: {e}")

    def _add_project_schedule(self, project_id: int, schedule: Dict):
        """Add a pipeline schedule to a project"""
        try:
            resolved_ref = self._resolve_branch(project_id, schedule.get('ref', 'main'))
            data = {
                'description': schedule.get('description', 'Pipeline schedule'),
                'cron': schedule.get('cron', '0 0 * * *'),
                'cron_timezone': schedule.get('cron_timezone', 'UTC'),
                'ref': resolved_ref,
                'active': schedule.get('active', True)
            }
            
            project = self.gl.projects.get(project_id)
            
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    project.pipelineschedules.create(data)
                    self.log("OK", f"Added schedule '{schedule.get('description')}' to project {project_id}")
                    return True
                except GitlabCreateError as e:
                    # 400 is expected on re-runs when schedule already exists
                    if "400" in str(e) or "already exists" in str(e).lower():
                        return True
                    
                    if attempt < max_attempts - 1:
                        self.log("INFO", f"Schedule creation failed, retrying... (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(2)
                    else:
                        raise
            
            return False
        except Exception as e:
            self.log("WARN", f"Failed to add schedule to project {project_id}: {e}")
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
        try:
            self.gl.auth()
            version = self.gl.version()
            self.log("OK", f"Connected to GitLab v{version}")
        except Exception as e:
            self.log("ERROR", f"Admin token is invalid or GitLab API is not responding: {e}")
            self.log("ERROR", "Please ensure GITLAB_ADMIN_TOKEN in .env is valid")
            return False
        
        # Check if current user is admin
        try:
            user = self.gl.user
            is_admin = getattr(user, 'is_admin', False)
            username = getattr(user, 'username', 'unknown')
            self.log("OK", f"Authenticated as {username} (admin: {is_admin})")
            
            if not is_admin:
                self.log("WARN", "Token user is not an admin - some operations may fail")
        except Exception as e:
            self.log("WARN", f"Could not verify admin status: {e}")
        
        # Create users (skip root as it already exists)
        self.log("INFO", "Creating users...")
        for user in config.get('users', []):
            if user['username'] != 'root':
                self.create_user(user)
            else:
                self.log("INFO", f"Skipping root user (already exists)")
                self.users_map['root'] = 1
        
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
    
    # Get config base path
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
