#!/usr/bin/env python3
"""
Scenario 4 deployment validation.
"""

from __future__ import annotations

import pytest

from .helpers import find_project, find_user, get_project_members, get_project_schedules, get_project_variable


pytestmark = [pytest.mark.deployment, pytest.mark.scenario_04]


def test_scenario_04_user_exists(api_session, gitlab_host_url: str):
    user = find_user(api_session, gitlab_host_url, "ci-breaker")
    assert user["email"] == "ci-breaker@lab.local"


def test_runner_breakout_lab_configuration(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "development-team/runner-breakout-lab")
    assert project["visibility"] == "private"

    members = get_project_members(api_session, gitlab_host_url, project["id"])
    ci_breaker = next(member for member in members if member["username"] == "ci-breaker")
    assert ci_breaker["access_level"] == 40

    objective = get_project_variable(api_session, gitlab_host_url, project["id"], "BREAKOUT_OBJECTIVE")
    assert "gl-runner-harvester" in objective["value"]
    assert objective["protected"] is False


def test_payroll_batch_recurring_flag_job(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "development-team/payroll-batch")
    assert project["visibility"] == "private"

    members = get_project_members(api_session, gitlab_host_url, project["id"])
    alice = next(member for member in members if member["username"] == "alice")
    assert alice["access_level"] == 50
    assert "ci-breaker" not in {member["username"] for member in members}

    schedule_list = get_project_schedules(api_session, gitlab_host_url, project["id"])
    schedule = next(item for item in schedule_list if item["description"] == "Payroll refresh every 5 minutes")
    assert schedule["cron"] == "*/5 * * * *"
    assert schedule["active"] is True

    flag = get_project_variable(api_session, gitlab_host_url, project["id"], "FLAG")
    assert flag["value"] == "flag{runner_abuse_5f3d91b2a4c7e8d1}"
    assert flag["protected"] is False
    assert flag["masked"] is False


def test_telemetry_batch_recurring_job(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "development-team/telemetry-batch")
    assert project["visibility"] == "private"

    schedule_list = get_project_schedules(api_session, gitlab_host_url, project["id"])
    schedule = next(item for item in schedule_list if item["description"] == "Telemetry refresh every 7 minutes")
    assert schedule["cron"] == "*/7 * * * *"
    assert schedule["active"] is True

    harvest_stream = get_project_variable(api_session, gitlab_host_url, project["id"], "HARVEST_STREAM")
    assert harvest_stream["value"] == "telemetry"
