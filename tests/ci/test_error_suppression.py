#!/usr/bin/env python3
"""
Unit tests for populate-gitlab.py error handling.
"""

import importlib.util
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from gitlab.exceptions import GitlabCreateError, GitlabGetError


pytestmark = pytest.mark.ci

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "scripts", "populate-gitlab.py")

spec = importlib.util.spec_from_file_location("populate_gitlab", SCRIPT_PATH)
populate_gitlab = importlib.util.module_from_spec(spec)
sys.modules["populate_gitlab"] = populate_gitlab
spec.loader.exec_module(populate_gitlab)


class TestSDKErrorHandling:
    @pytest.fixture
    def populator(self):
        with patch("populate_gitlab.gitlab.Gitlab"):
            populator = populate_gitlab.GitLabPopulator("http://localhost", "test-token")
            populator.users_map = {"alice": 1, "bob": 2, "developer": 6}
            populator.groups_map = {"security-team": 7}
            populator.projects_map = {"web-service": 6}
            return populator

    def test_add_group_member_handles_conflict(self, populator):
        with patch.object(populator.gl, "groups") as mock_groups:
            mock_group = MagicMock()
            mock_groups.get.return_value = mock_group
            mock_group.members.create.side_effect = GitlabCreateError("409 Conflict: Member already exists")
            populator._add_group_member(7, {"username": "alice", "access_level": 30})
            mock_group.members.create.assert_called_once()

    def test_add_project_member_handles_conflict(self, populator):
        with patch.object(populator.gl, "projects") as mock_projects:
            mock_project = MagicMock()
            mock_projects.get.return_value = mock_project
            mock_project.members.create.side_effect = GitlabCreateError("409 Conflict: Member already exists")
            populator._add_project_member(6, {"username": "bob", "access_level": 30})
            mock_project.members.create.assert_called_once()

    def test_add_project_schedule_handles_duplicate(self, populator):
        with patch.object(populator, "_resolve_branch", return_value="main"):
            with patch.object(populator.gl, "projects") as mock_projects:
                mock_project = MagicMock()
                mock_projects.get.return_value = mock_project
                mock_project.pipelineschedules.create.side_effect = GitlabCreateError(
                    "400 Bad Request: Schedule already exists"
                )

                result = populator._add_project_schedule(
                    6,
                    {"description": "Build", "cron": "*/2 * * * *", "ref": "main", "active": True},
                )
                assert result is True

    def test_add_project_variable_creates_new(self, populator):
        with patch.object(populator.gl, "projects") as mock_projects:
            mock_project = MagicMock()
            mock_projects.get.return_value = mock_project
            mock_project.variables.get.side_effect = GitlabGetError("404 Not Found")
            mock_project.variables.create.return_value = MagicMock()

            populator._add_project_variable(
                6,
                {"key": "TEST_VAR", "value": "test-value", "protected": False, "masked": False},
            )
            mock_project.variables.create.assert_called_once()

    def test_add_project_variable_updates_existing(self, populator):
        with patch.object(populator.gl, "projects") as mock_projects:
            mock_project = MagicMock()
            mock_projects.get.return_value = mock_project
            mock_var = MagicMock()
            mock_project.variables.get.return_value = mock_var

            populator._add_project_variable(
                6,
                {"key": "TEST_VAR", "value": "new-value", "protected": False, "masked": False},
            )
            assert mock_var.value == "new-value"
            mock_var.save.assert_called_once()

    def test_create_project_idempotent_with_repo_files(self, populator):
        with patch.object(populator.gl, "projects") as mock_projects:
            existing_project = MagicMock()
            existing_project.id = 6
            existing_project.path = "web-service"
            existing_project.default_branch = "main"
            mock_projects.list.return_value = [existing_project]

            with patch.object(populator, "_create_file") as mock_create_file:
                result = populator.create_project(
                    {
                        "name": "Web Service",
                        "path": "web-service",
                        "description": "Web service",
                        "visibility": "public",
                        "members": [],
                        "variables": [],
                        "schedules": [],
                        "repo_files": [{"path": "renovate.json", "content": "{}"}],
                    }
                )

            assert result == 6
            mock_projects.create.assert_not_called()
            mock_create_file.assert_called_once()


class TestPATCreation:
    @pytest.fixture
    def populator(self):
        with patch("populate_gitlab.gitlab.Gitlab"):
            populator = populate_gitlab.GitLabPopulator("http://localhost", "test-token")
            populator.users_map = {"developer": 6}
            return populator

    def test_pat_creation_success(self, populator):
        with patch.object(populator.gl, "users") as mock_users:
            mock_user = MagicMock()
            mock_users.get.return_value = mock_user
            mock_token = MagicMock()
            mock_token.token = "glpat-test-token-123456789"
            mock_user.personal_access_tokens.create.return_value = mock_token

            result = populator._create_personal_access_token(
                6,
                "developer",
                "automation-token",
                "automation",
                scopes=["api", "read_user"],
            )

            assert result == "glpat-test-token-123456789"
            assert populator.user_tokens["developer:automation"] == "glpat-test-token-123456789"

    def test_pat_creation_failure(self, populator):
        with patch.object(populator.gl, "users") as mock_users:
            mock_user = MagicMock()
            mock_users.get.return_value = mock_user
            mock_user.personal_access_tokens.create.side_effect = Exception("API Error")

            result = populator._create_personal_access_token(
                6,
                "developer",
                "automation-token",
                "automation",
            )

            assert result is None
