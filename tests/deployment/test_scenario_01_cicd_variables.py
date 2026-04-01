#!/usr/bin/env python3
"""
Scenario 1 deployment validation.
"""

import pytest

from .helpers import find_project, find_user, get_project_members, get_project_schedules, get_project_variable


pytestmark = [pytest.mark.deployment, pytest.mark.scenario_01]


def test_scenario_01_user_exists(api_session, gitlab_host_url: str):
    user = find_user(api_session, gitlab_host_url, "developer")
    assert user["email"] == "developer@lab.local"


def test_scenario_01_project_exists(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "root/qa-automation")
    assert project["visibility"] == "public"


def test_scenario_01_membership(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "root/qa-automation")
    members = get_project_members(api_session, gitlab_host_url, project["id"])
    developer = next(member for member in members if member["username"] == "developer")
    assert developer["access_level"] == 30


def test_scenario_01_variable(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "root/qa-automation")
    variable = get_project_variable(api_session, gitlab_host_url, project["id"], "XKEY")
    assert variable["value"] == "flag{cicd_vars_d78d62cc4824fa8f}"
    assert variable["protected"] is False
    assert variable["masked"] is False


def test_scenario_01_schedule(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "root/qa-automation")
    schedules = get_project_schedules(api_session, gitlab_host_url, project["id"])
    schedule = next(item for item in schedules if item["description"] == "QA tests every 30 minutes")
    assert schedule["cron"] == "*/30 * * * *"
    assert schedule["active"] is True
