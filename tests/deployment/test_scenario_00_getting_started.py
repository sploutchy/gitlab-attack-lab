#!/usr/bin/env python3
"""
Scenario 0 deployment validation.
"""

import pytest

from .helpers import find_project, get_project_variable


pytestmark = [pytest.mark.deployment, pytest.mark.scenario_00]


def test_security_tools_project_exists(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "security-team/security-tools")
    assert project["visibility"] == "private"


def test_security_tools_has_intro_flag(api_session, gitlab_host_url: str):
    project = find_project(api_session, gitlab_host_url, "security-team/security-tools")
    variable = get_project_variable(api_session, gitlab_host_url, project["id"], "INTRO_FLAG")
    assert variable["value"].startswith("flag{welcome_")
    assert variable["protected"] is False
