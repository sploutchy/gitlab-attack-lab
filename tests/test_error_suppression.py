"""
Tests for error suppression logic in populate-gitlab.py
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

# Import the module - note the hyphen in filename
import importlib.util
spec = importlib.util.spec_from_file_location("populate_gitlab", "scripts/populate-gitlab.py")
populate_gitlab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(populate_gitlab)

GitLabPopulator = populate_gitlab.GitLabPopulator


class TestErrorSuppression:
    """Test error suppression in API calls"""
    
    @pytest.fixture
    def populator(self):
        """Create a GitLabPopulator instance"""
        return GitLabPopulator('http://test-gitlab', 'test-token')
    
    def test_suppress_404_on_variable_check(self, populator):
        """Test that 404 errors are suppressed when checking if variable exists"""
        with patch.object(populator.session, 'get') as mock_get:
            # Simulate 404 response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = '{"message":"404 Not Found"}'
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            # Call should return None without logging error
            result = populator.api_call('GET', 'projects/1/variables/TEST', suppress_errors=[404])
            
            assert result is None
    
    def test_suppress_409_on_member_add(self, populator):
        """Test that 409 Conflict errors are suppressed when adding members"""
        with patch.object(populator.session, 'post') as mock_post:
            # Simulate 409 response
            mock_response = Mock()
            mock_response.status_code = 409
            mock_response.text = '{"message":"Member already exists"}'
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            mock_post.return_value = mock_response
            
            # Call should return None without logging error
            result = populator.api_call('POST', 'projects/1/members', {'user_id': 1}, suppress_errors=[409])
            
            assert result is None
    
    def test_suppress_400_on_schedule_create(self, populator):
        """Test that 400 Bad Request errors are suppressed when creating duplicate schedules"""
        with patch.object(populator.session, 'post') as mock_post:
            # Simulate 400 response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = '{"message":"Schedule already exists"}'
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            mock_post.return_value = mock_response
            
            # Call should return None without logging error
            result = populator.api_call('POST', 'projects/1/pipeline_schedules', {}, suppress_errors=[400])
            
            assert result is None
    
    def test_no_suppress_without_parameter(self, populator):
        """Test that errors are logged when suppress_errors is not provided"""
        with patch.object(populator.session, 'get') as mock_get:
            with patch.object(populator, 'log') as mock_log:
                # Simulate 404 response
                mock_response = Mock()
                mock_response.status_code = 404
                mock_response.text = '{"message":"404 Not Found"}'
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
                mock_get.return_value = mock_response
                
                # Call without suppress_errors should log error
                result = populator.api_call('GET', 'projects/1/variables/TEST')
                
                assert result is None
                # Check that log was called with ERROR
                mock_log.assert_called()
                call_args = mock_log.call_args[0]
                assert call_args[0] == 'ERROR'
    
    def test_suppress_multiple_status_codes(self, populator):
        """Test that multiple status codes can be suppressed"""
        with patch.object(populator.session, 'get') as mock_get:
            # Simulate 404 response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = '{"message":"404 Not Found"}'
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            # Should suppress both 404 and 409
            result = populator.api_call('GET', 'test', suppress_errors=[404, 409])
            
            assert result is None
    
    def test_add_group_member_suppresses_409(self, populator):
        """Test that _add_group_member suppresses 409 Conflict errors"""
        populator.users_map = {'testuser': 1}
        
        with patch.object(populator, 'api_call') as mock_api:
            mock_api.return_value = None  # Simulates suppressed 409
            
            # Should not raise or log warning
            populator._add_group_member(1, {'username': 'testuser', 'access_level': 30})
            
            # Verify suppress_errors=[409] was passed
            mock_api.assert_called_once()
            call_args = mock_api.call_args
            assert call_args[1]['suppress_errors'] == [409]
    
    def test_add_project_member_suppresses_409(self, populator):
        """Test that _add_project_member suppresses 409 Conflict errors"""
        populator.users_map = {'testuser': 1}
        
        with patch.object(populator, 'api_call') as mock_api:
            mock_api.return_value = None  # Simulates suppressed 409
            
            # Should not raise or log warning
            populator._add_project_member(1, {'username': 'testuser', 'access_level': 30})
            
            # Verify suppress_errors=[409] was passed
            mock_api.assert_called_once()
            call_args = mock_api.call_args
            assert call_args[1]['suppress_errors'] == [409]
    
    def test_add_project_schedule_suppresses_400(self, populator):
        """Test that _add_project_schedule suppresses 400 Bad Request errors"""
        with patch.object(populator, 'api_call') as mock_api:
            with patch.object(populator, '_resolve_branch') as mock_resolve:
                mock_resolve.return_value = 'main'
                mock_api.return_value = None  # Simulates suppressed 400
                
                # Should not raise
                result = populator._add_project_schedule(1, {
                    'description': 'Test schedule',
                    'cron': '0 0 * * *'
                })
                
                # Verify suppress_errors=[400] was passed
                assert mock_api.call_count == 3  # 3 retry attempts
                for call in mock_api.call_args_list:
                    if 'suppress_errors' in call[1]:
                        assert call[1]['suppress_errors'] == [400]
    
    def test_variable_check_uses_suppress_errors(self, populator):
        """Test that variable existence check uses suppress_errors=[404]"""
        with patch.object(populator, 'api_call') as mock_api:
            mock_api.side_effect = [None, {'id': 1}]  # First call (GET) returns None, second (POST) succeeds
            
            populator._add_project_variable(1, {
                'key': 'TEST_VAR',
                'value': 'test_value',
                'protected': False,
                'masked': False
            })
            
            # First call should be GET with suppress_errors=[404]
            first_call = mock_api.call_args_list[0]
            assert first_call[0][0] == 'GET'
            assert 'variables/' in first_call[0][1]
            assert first_call[1]['suppress_errors'] == [404]
    
    def test_branch_check_uses_suppress_errors(self, populator):
        """Test that branch existence check uses suppress_errors=[404]"""
        with patch.object(populator, 'api_call') as mock_api:
            mock_api.side_effect = [None, {'default_branch': 'main'}, {'name': 'main'}]
            
            result = populator._resolve_branch(1, 'main')
            
            # First call should check for 'main' branch with suppress_errors=[404]
            first_call = mock_api.call_args_list[0]
            assert 'repository/branches/' in first_call[0][1]
            assert first_call[1]['suppress_errors'] == [404]
    
    def test_file_check_uses_suppress_errors(self, populator):
        """Test that file existence check uses suppress_errors=[404]"""
        with patch.object(populator, 'api_call') as mock_api:
            with patch.object(populator, '_resolve_branch') as mock_resolve:
                mock_resolve.return_value = 'main'
                mock_api.side_effect = [None, {'file_path': '.gitlab-ci.yml'}]  # GET returns None, POST succeeds
                
                populator._create_file(1, '.gitlab-ci.yml', 'content', 'main', 'Add CI')
                
                # First call should be GET with suppress_errors=[404]
                first_call = mock_api.call_args_list[0]
                assert first_call[0][0] == 'GET'
                assert 'repository/files/' in first_call[0][1]
                assert first_call[1]['suppress_errors'] == [404]
    
    def test_successful_api_call_returns_data(self, populator):
        """Test that successful API calls return data even with suppress_errors"""
        with patch.object(populator.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"id": 1, "name": "test"}'
            mock_response.json.return_value = {"id": 1, "name": "test"}
            mock_get.return_value = mock_response
            
            result = populator.api_call('GET', 'test', suppress_errors=[404])
            
            assert result == {"id": 1, "name": "test"}
    
    def test_unsuppressed_error_still_logged(self, populator):
        """Test that errors not in suppress_errors list are still logged"""
        with patch.object(populator.session, 'get') as mock_get:
            with patch.object(populator, 'log') as mock_log:
                # Simulate 500 response
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.text = '{"message":"Internal Server Error"}'
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
                mock_get.return_value = mock_response
                
                # Call with suppress_errors=[404] should still log 500 error
                result = populator.api_call('GET', 'test', suppress_errors=[404])
                
                assert result is None
                # Check that error was logged
                mock_log.assert_called()
                call_args = mock_log.call_args[0]
                assert call_args[0] == 'ERROR'
                assert '500' in call_args[1]
