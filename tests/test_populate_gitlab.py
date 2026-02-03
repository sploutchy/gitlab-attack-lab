"""
Comprehensive tests for populate-gitlab.py error handling and suppression logic
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests
import sys
import os
import importlib.util

# Load populate-gitlab.py module
spec = importlib.util.spec_from_file_location("populate_gitlab", 
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'populate-gitlab.py'))
populate_gitlab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(populate_gitlab)

GitLabPopulator = populate_gitlab.GitLabPopulator


class MockResponse:
    """Mock response object"""
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self.json_data = json_data or {}
        self.text = text
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)


class TestErrorSuppression:
    """Test error suppression for expected API errors"""
    
    @pytest.fixture
    def populator(self):
        """Create a GitLabPopulator instance for testing"""
        with patch.object(populate_gitlab.requests, 'Session'):
            populator = GitLabPopulator('http://localhost', 'test-token')
            populator.users_map = {'testuser': 1}
            return populator
    
    def test_404_suppression_on_variables_lookup(self, populator):
        """Test that 404 errors on variable existence checks are suppressed"""
        with patch.object(populator.session, 'get') as mock_get:
            # Mock a 404 response for variable lookup
            error_response = MockResponse(status_code=404, text='{"message": "Not Found"}')
            mock_get.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            # Call with suppress_errors=[404]
            result = populator.api_call('GET', 'projects/1/variables/TEST_VAR', suppress_errors=[404])
            
            # Should return None without logging error
            assert result is None
    
    def test_404_suppression_on_branches_lookup(self, populator):
        """Test that 404 errors on branch existence checks are suppressed"""
        with patch.object(populator.session, 'get') as mock_get:
            error_response = MockResponse(status_code=404, text='{"message": "Not Found"}')
            mock_get.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            result = populator.api_call('GET', 'projects/1/repository/branches/main', suppress_errors=[404])
            
            assert result is None
    
    def test_404_suppression_on_files_lookup(self, populator):
        """Test that 404 errors on file existence checks are suppressed"""
        with patch.object(populator.session, 'get') as mock_get:
            error_response = MockResponse(status_code=404, text='{"message": "Not Found"}')
            mock_get.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            result = populator.api_call('GET', 'projects/1/repository/files/test.txt', suppress_errors=[404])
            
            assert result is None
    
    def test_409_suppression_on_group_member_addition(self, populator):
        """Test that 409 Conflict errors when adding group members are suppressed"""
        with patch.object(populator.session, 'post') as mock_post:
            error_response = MockResponse(status_code=409, text='{"message": "Member already exists"}')
            mock_post.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            result = populator.api_call('POST', 'groups/1/members', {'user_id': 1}, suppress_errors=[409])
            
            assert result is None
    
    def test_409_suppression_on_project_member_addition(self, populator):
        """Test that 409 Conflict errors when adding project members are suppressed"""
        with patch.object(populator.session, 'post') as mock_post:
            error_response = MockResponse(status_code=409, text='{"message": "Member already exists"}')
            mock_post.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            result = populator.api_call('POST', 'projects/1/members', {'user_id': 1}, suppress_errors=[409])
            
            assert result is None
    
    def test_400_suppression_on_schedule_creation(self, populator):
        """Test that 400 errors when creating duplicate schedules are suppressed"""
        with patch.object(populator.session, 'post') as mock_post:
            error_response = MockResponse(status_code=400, text='{"message": "Schedule already exists"}')
            mock_post.side_effect = requests.exceptions.HTTPError(response=error_response)
            
            result = populator.api_call('POST', 'projects/1/pipeline_schedules', 
                                       {'description': 'test'}, suppress_errors=[400])
            
            assert result is None


class TestMemberAddition:
    """Test member addition with error suppression"""
    
    @pytest.fixture
    def populator(self):
        """Create a GitLabPopulator instance for testing"""
        with patch.object(populate_gitlab.requests, 'Session'):
            populator = GitLabPopulator('http://localhost', 'test-token')
            populator.users_map = {'alice': 1, 'bob': 2}
            return populator
    
    def test_group_member_addition_success(self, populator):
        """Test successful group member addition"""
        with patch.object(populator, 'api_call') as mock_api:
            mock_api.return_value = {'id': 1, 'user_id': 1}
            
            populator._add_group_member(1, {'username': 'alice', 'access_level': 30})
            
            # Verify api_call was made with suppress_errors=[409]
            mock_api.assert_called_once_with('POST', 'groups/1/members', 
                                            {'user_id': 1, 'access_level': 30}, 
                                            suppress_errors=[409])
    
    def test_group_member_addition_conflict_on_rerun(self, populator):
        """Test that 409 Conflict on group member addition (re-run) is handled silently"""
        with patch.object(populator, 'api_call') as mock_api:
            # Simulate 409 Conflict (member already exists)
            mock_api.return_value = None  # suppress_errors=[409] returns None
            
            # Should not raise exception or log warning
            populator._add_group_member(1, {'username': 'alice', 'access_level': 30})
            
            mock_api.assert_called_once()
    
    def test_project_member_addition_success(self, populator):
        """Test successful project member addition"""
        with patch.object(populator, 'api_call') as mock_api:
            mock_api.return_value = {'id': 1, 'user_id': 2}
            
            populator._add_project_member(5, {'username': 'bob', 'access_level': 40})
            
            # Verify api_call was made with suppress_errors=[409]
            mock_api.assert_called_once_with('POST', 'projects/5/members', 
                                            {'user_id': 2, 'access_level': 40}, 
                                            suppress_errors=[409])
    
    def test_project_member_addition_conflict_on_rerun(self, populator):
        """Test that 409 Conflict on project member addition (re-run) is handled silently"""
        with patch.object(populator, 'api_call') as mock_api:
            mock_api.return_value = None  # suppress_errors=[409] returns None
            
            populator._add_project_member(5, {'username': 'bob', 'access_level': 40})
            
            mock_api.assert_called_once()
    
    def test_member_not_found_warning(self, populator):
        """Test that warning is logged when user doesn't exist"""
        with patch.object(populator, 'log') as mock_log:
            populator._add_project_member(5, {'username': 'nonexistent', 'access_level': 30})
            
            # Should log warning about user not found
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert 'WARN' in call_args
            assert 'nonexistent' in call_args[1]


class TestScheduleAddition:
    """Test schedule addition with error suppression"""
    
    @pytest.fixture
    def populator(self):
        """Create a GitLabPopulator instance for testing"""
        with patch.object(populate_gitlab.requests, 'Session'):
            populator = GitLabPopulator('http://localhost', 'test-token')
            return populator
    
    def test_schedule_creation_success(self, populator):
        """Test successful schedule creation"""
        with patch.object(populator, 'api_call') as mock_api, \
             patch.object(populator, '_resolve_branch') as mock_branch:
            
            mock_api.return_value = {'id': 1, 'description': 'test'}
            mock_branch.return_value = 'main'
            
            schedule_data = {
                'description': 'Build every 2 minutes',
                'cron': '*/2 * * * *',
                'cron_timezone': 'UTC',
                'ref': 'main',
                'active': True
            }
            
            populator._add_project_schedule(1, schedule_data)
            
            # Verify api_call was made with suppress_errors=[400]
            call_args = mock_api.call_args
            assert call_args[0][0] == 'POST'
            assert 'pipeline_schedules' in call_args[0][1]
            assert 'suppress_errors' in call_args[1]
            assert call_args[1]['suppress_errors'] == [400]
    
    def test_schedule_creation_duplicate_on_rerun(self, populator):
        """Test that 400 Bad Request on duplicate schedule (re-run) is suppressed"""
        with patch.object(populator, '_resolve_branch') as mock_branch:
            mock_branch.return_value = 'main'
            
            with patch.object(populator.session, 'post') as mock_post:
                # Mock 400 response for duplicate schedule
                error_response = MockResponse(status_code=400, text='{"message": "Schedule already exists"}')
                mock_post.side_effect = requests.exceptions.HTTPError(response=error_response)
                
                schedule_data = {
                    'description': 'Build every 2 minutes',
                    'cron': '*/2 * * * *',
                    'ref': 'main'
                }
                
                # The retry logic should attempt 3 times and then return False
                result = populator._add_project_schedule(1, schedule_data)
                
                assert result is False
                # Verify retries happened
                assert mock_post.call_count == 3


class TestVariableAddition:
    """Test variable addition and conflict handling"""
    
    @pytest.fixture
    def populator(self):
        """Create a GitLabPopulator instance for testing"""
        with patch.object(populate_gitlab.requests, 'Session'):
            populator = GitLabPopulator('http://localhost', 'test-token')
            return populator
    
    def test_variable_creation_with_404_on_existence_check(self, populator):
        """Test that 404 on variable existence check is suppressed"""
        with patch.object(populator, 'api_call') as mock_api:
            # First call: 404 (variable doesn't exist) - suppressed
            # Second call: Success (create variable)
            mock_api.side_effect = [None, {'key': 'TEST', 'value': 'test'}]
            
            variable = {
                'key': 'TEST_VAR',
                'value': 'test_value',
                'protected': False,
                'masked': False
            }
            
            populator._add_project_variable(1, variable)
            
            # Should have been called twice: once to check, once to create
            assert mock_api.call_count == 2
            # First call should have suppress_errors=[404]
            first_call = mock_api.call_args_list[0]
            assert 'suppress_errors' in first_call[1]
            assert first_call[1]['suppress_errors'] == [404]


class TestIdempotentOperations:
    """Test idempotent re-run behavior"""
    
    @pytest.fixture
    def populator(self):
        """Create a GitLabPopulator instance for testing"""
        with patch.object(populate_gitlab.requests, 'Session'):
            populator = GitLabPopulator('http://localhost', 'test-token')
            populator.users_map = {'developer': 1}
            return populator
    
    def test_project_creation_rerun_skips_redundant_ops(self, populator):
        """Test that on re-run, we still attempt members/variables (with error suppression)"""
        with patch.object(populator, 'api_call') as mock_api:
            # First call: GET projects (returns existing)
            # Then calls to add members and variables
            mock_api.side_effect = [
                [{'id': 1, 'path': 'test-project'}],  # GET projects?search=
                None,  # POST members with suppress_errors=[409]
                None,  # GET variables with suppress_errors=[404]
                None,  # POST variables
            ]
            
            with patch.object(populator, '_resolve_branch'):
                with patch.object(populator, '_load_ci_template_file'):
                    with patch.object(populator, '_create_file'):
                        with patch.object(populator, '_add_project_schedule'):
                            project = {
                                'name': 'test',
                                'path': 'test-project',
                                'visibility': 'public',
                                'members': [{'username': 'developer', 'access_level': 30}],
                                'variables': [{'key': 'TEST', 'value': 'val', 'protected': False, 'masked': False}],
                                'ci_cd_template': 'ci-templates/test.yml'
                            }
                            
                            result = populator.create_project(project)
                            
                            # Project should still be processed
                            assert result == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
