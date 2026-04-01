#!/usr/bin/env python3
"""
Scenario 2 deployment validation.
"""

import pytest

from .helpers import find_project, find_user, get_project_members, get_project_schedules, get_project_variable


pytestmark = [pytest.mark.deployment, pytest.mark.scenario_02]


def test_scenario_02_user_exists(api_session, gitlab_host_url: str):
    user = find_user(api_session, gitlab_host_url, "test-manager")
    assert user["email"] == "test-manager@lab.local"


def test_web_service_project_configuration(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "root/web-service")
    assert project["visibility"] == "public"

    members = get_project_members(api_session, gitlab_host_url, project["id"])
    owner = next(member for member in members if member["username"] == "test-manager")
    assert owner["access_level"] == 50

    variable = get_project_variable(api_session, gitlab_host_url, project["id"], "GL_PAT")
    assert variable["value"].startswith("glpat-")
    assert variable["protected"] is False
    assert variable["masked"] is False

    schedules = get_project_schedules(api_session, gitlab_host_url, project["id"])
    schedule = next(item for item in schedules if item["description"] == "Private data validation every 30 minutes")
    assert schedule["cron"] == "*/30 * * * *"


def test_private_test_data_configuration(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "root/private-test-data")
    assert project["visibility"] == "private"

    members = get_project_members(api_session, gitlab_host_url, project["id"])
    owner = next(member for member in members if member["username"] == "test-manager")
    assert owner["access_level"] == 50

    unused_flag = get_project_variable(api_session, gitlab_host_url, project["id"], "UNUSED_FLAG_TOKEN")
    assert unused_flag["value"] == "flag{unused_43f5e00b0cec678f}"
    assert unused_flag["protected"] is False

    testing_token = get_project_variable(api_session, gitlab_host_url, project["id"], "TESTING_TOKEN")
    assert testing_token["value"] == "flag{lateral_movement_589fd9ddb5b21182}"
    assert testing_token["protected"] is True
    assert testing_token["masked"] is False
