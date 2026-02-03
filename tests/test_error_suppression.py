#!/usr/bin/env python3
"""
Unit tests for error handling in the refactored GitLab SDK-based populator
Tests the SDK exception handling and idempotency features
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import importlib.util

# Load populate-gitlab.py with hyphen in the name
spec = importlib.util.spec_from_file_location(
    "populate_gitlab",
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'populate-gitlab.py')
)
populate_gitlab = importlib.util.module_from_spec(spec)
sys.modules["populate_gitlab"] = populate_gitlab
spec.loader.exec_module(populate_gitlab)

from gitlab.exceptions import GitlabGetError, GitlabCreateError


class TestSDKErrorHandling:
    """Test error handling with python-gitlab SDK"""
    
    @pytest.fixture
    def populator(self):
        """Create a GitLabPopulator instance for testing"""
        with patch('populate_gitlab.gitlab.Gitlab'):
            populator = populate_gitlab.GitLabPopulator('http://localhost', 'test-token')
            populator.users_map = {'alice': 1, 'bob': 2, 'developer': 6}
            populator.groups_map = {'security-team': 7}
            populator.projects_map = {'web-service': 6}
            return populator
    
    def test_add_group_member_handles_conflict(self, populator):
        """Test that 409 Conflict (member exists) is handled silently"""
        with patch.object(populator.gl, 'groups') as mock_groups:
            mock_group = MagicMock()
            mock_groups.get.return_value = mock_group
            
            # Simulate 409 Conflict when adding member
            mock_group.members.create.side_effect = GitlabCreateError('409 Conflict: Member already exists')
            
            # Should not raise, just log
            populator._add_group_member(7, {'username': 'alice', 'access_level': 30})
            
            # Verify it was called
            mock_group.members.create.assert_called_once()
    
    def test_add_project_member_handles_conflict(self, populator):
        """Test that 409 Conflict (member exists) is handled silently"""
        with patch.object(populator.gl, 'projects') as mock_projects:
            mock_project = MagicMock()
            mock_projects.get.return_value = mock_project
            
            # Simulate 409 Conflict when adding member
            mock_project.members.create.side_effect = GitlabCreateError('409 Conflict: Member already exists')
            
            # Should not raise, just log
            populator._add_project_member(6, {'username': 'bob', 'access_level': 30})
            
            # Verify it was called
            mock_project.members.create.assert_called_once()
    
    def test_add_project_schedule_handles_duplicate(self, populator):
        """Test that duplicate schedule (400) is handled silently"""
        with patch.object(populator, '_resolve_branch') as mock_resolve:
            mock_resolve.return_value = 'main'
            
            with patch.object(populator.gl, 'projects') as mock_projects:
                mock_project = MagicMock()
                mock_projects.get.return_value = mock_project
                
                # Simulate 400 Bad Request when schedule already exists
                mock_project.pipelineschedules.create.side_effect = GitlabCreateError('400 Bad Request: Schedule already exists')
                
                # Should not raise, just return silently
                result = populator._add_project_schedule(
                    6, 
                    {'description': 'Build', 'cron': '*/2 * * * *', 'ref': 'main', 'active': True}
                )
                
                assert result is True  # Returns True even on duplicate
    
    def test_add_project_variable_creates_new(self, populator):
        """Test successful variable creation"""
        with patch.object(populator.gl, 'projects') as mock_projects:
            mock_project = MagicMock()
            mock_projects.get.return_value = mock_project
            
            # Variable doesn't exist
            mock_project.variables.get.side_effect = GitlabGetError('404 Not Found')
            mock_project.variables.create.return_value = MagicMock()
            
            populator._add_project_variable(6, {
                'key': 'TEST_VAR',
                'value': 'test-value',
                'protected': False,
                'masked': False
            })
            
            # Verify create was called
            mock_project.variables.create.assert_called_once()
    
    def test_add_project_variable_updates_existing(self, populator):
        """Test variable update when it already exists"""
        with patch.object(populator.gl, 'projects') as mock_projects:
            mock_project = MagicMock()
            mock_projects.get.return_value = mock_project
            
            # Variable exists
            mock_var = MagicMock()
            mock_project.variables.get.return_value = mock_var
            
            populator._add_project_variable(6, {
                'key': 'TEST_VAR',
                'value': 'new-value',
                'protected': False,
                'masked': False
            })
            
            # Verify variable was updated
            assert mock_var.value == 'new-value'
            mock_var.save.assert_called_once()
    
    def test_create_user_idempotent(self, populator):
        """Test that creating an existing user doesn't fail"""
        with patch.object(populator.gl, 'users') as mock_users:
            # User already exists
            existing_user = MagicMock()
            existing_user.id = 6
            mock_users.list.return_value = [existing_user]
            
            result = populator.create_user({
                'username': 'developer',
                'email': 'dev@lab.local',
                'password': 'password',
                'name': 'Developer'
            })
            
            # Should return existing user ID
            assert result == 6
            # Should not create new user
            mock_users.create.assert_not_called()
    
    def test_create_group_idempotent(self, populator):
        """Test that creating an existing group doesn't fail"""
        with patch.object(populator.gl, 'groups') as mock_groups:
            # Group already exists
            existing_group = MagicMock()
            existing_group.id = 7
            existing_group.path = 'security-team'
            existing_group.members.get.return_value = []
            mock_groups.list.return_value = [existing_group]
            
            result = populator.create_group({
                'name': 'Security Team',
                'path': 'security-team',
                'description': 'Security team',
                'visibility': 'private',
                'members': []
            })
            
            # Should return existing group ID
            assert result == 7
            # Should not create new group
            mock_groups.create.assert_not_called()
    
    def test_create_project_idempotent(self, populator):
        """Test that creating an existing project doesn't fail"""
        with patch.object(populator.gl, 'projects') as mock_projects:
            # Project already exists
            existing_project = MagicMock()
            existing_project.id = 6
            existing_project.path = 'web-service'
            existing_project.default_branch = 'main'
            mock_projects.list.return_value = [existing_project]
            
            result = populator.create_project({
                'name': 'Web Service',
                'path': 'web-service',
                'description': 'Web service',
                'visibility': 'public',
                'members': [],
                'variables': [],
                'schedules': []
            })
            
            # Should return existing project ID
            assert result == 6
            # Should not create new project
            mock_projects.create.assert_not_called()


class TestPATCreation:
    """Test personal access token creation with SDK"""
    
    @pytest.fixture
    def populator(self):
        """Create a GitLabPopulator instance for testing"""
        with patch('populate_gitlab.gitlab.Gitlab'):
            populator = populate_gitlab.GitLabPopulator('http://localhost', 'test-token')
            populator.users_map = {'developer': 6}
            return populator
    
    def test_pat_creation_success(self, populator):
        """Test successful PAT creation"""
        with patch.object(populator.gl, 'users') as mock_users:
            mock_user = MagicMock()
            mock_users.get.return_value = mock_user
            
            # Mock PAT creation
            mock_token = MagicMock()
            mock_token.token = 'glpat-test-token-123456789'
            mock_user.personal_access_tokens.create.return_value = mock_token
            
            result = populator._create_personal_access_token(
                6, 'developer', 'automation-token', 'automation',
                scopes=['api', 'read_user']
            )
            
            assert result == 'glpat-test-token-123456789'
            assert populator.user_tokens['developer:automation'] == 'glpat-test-token-123456789'
    
    def test_pat_creation_failure(self, populator):
        """Test PAT creation failure handling"""
        with patch.object(populator.gl, 'users') as mock_users:
            mock_user = MagicMock()
            mock_users.get.return_value = mock_user
            
            # Simulate failure
            mock_user.personal_access_tokens.create.side_effect = Exception('API Error')
            
            result = populator._create_personal_access_token(
                6, 'developer', 'automation-token', 'automation'
            )
            
            assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
