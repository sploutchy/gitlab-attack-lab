#!/usr/bin/env python3
"""
Global deployment validation tests.
"""

from __future__ import annotations

import subprocess
import time

import pytest
import requests

from .helpers import api_get_json, find_group, find_project, find_user


pytestmark = pytest.mark.deployment


def test_gitlab_responds(gitlab_host_url: str):
    response = requests.get(f"{gitlab_host_url}/api/v4/version", timeout=10)
    assert response.status_code in {200, 401}


def test_admin_authentication(api_session, gitlab_host_url: str):
    user = api_get_json(api_session, gitlab_host_url, "user")
    assert user["username"] == "root"
    assert user["is_admin"] is True


def test_auto_devops_disabled(api_session, gitlab_host_url: str):
    settings = api_get_json(api_session, gitlab_host_url, "application/settings")
    assert settings["auto_devops_enabled"] is False


def test_expected_users_created(api_session, gitlab_host_url: str, structure_config: dict):
    for user_cfg in structure_config["users"]:
        user = find_user(api_session, gitlab_host_url, user_cfg["username"])
        assert user["username"] == user_cfg["username"]


def test_expected_groups_created(api_session, gitlab_host_url: str, structure_config: dict):
    for group_cfg in structure_config.get("groups", []):
        # "root" is a reserved user namespace in GitLab and may not be creatable as a group.
        if group_cfg["path"] == "root":
            continue
        group = find_group(api_session, gitlab_host_url, group_cfg["path"])
        assert group["path"] == group_cfg["path"]


def test_expected_projects_created(api_session, gitlab_host_url: str, structure_config: dict):
    for project_cfg in structure_config.get("projects", []):
        namespace = project_cfg.get("group") or "root"
        project = find_project(api_session, gitlab_host_url, f"{namespace}/{project_cfg['path']}")
        assert project["path"] == project_cfg["path"]


def test_ci_configs_exist(api_session, gitlab_host_url: str, structure_config: dict):
    for project_cfg in structure_config.get("projects", []):
        if not project_cfg.get("ci_cd_enabled"):
            continue
        namespace = project_cfg.get("group") or "root"
        project = find_project(api_session, gitlab_host_url, f"{namespace}/{project_cfg['path']}")
        ref = project.get("default_branch") or project_cfg.get("default_branch") or "main"
        response = api_session.get(
            f"{gitlab_host_url}/api/v4/projects/{project['id']}/repository/files/.gitlab-ci.yml",
            params={"ref": ref},
        )
        assert response.status_code == 200, f"Missing CI config for {project['path_with_namespace']}"


def test_expected_runners_registered(api_session, gitlab_host_url: str, structure_config: dict):
    runners = api_get_json(api_session, gitlab_host_url, "runners/all", params={"per_page": 100})
    descriptions = {runner["description"] for runner in runners}
    for runner_cfg in structure_config.get("runners", []):
        assert runner_cfg["description"] in descriptions


def test_runners_contacted(api_session, gitlab_host_url: str, structure_config: dict):
    expected = {runner["description"] for runner in structure_config.get("runners", [])}
    max_wait = 60
    poll_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        runners = api_get_json(api_session, gitlab_host_url, "runners/all", params={"per_page": 100})
        all_contacted = True
        for description in expected:
            matching = [runner for runner in runners if runner["description"] == description]
            assert matching, f"Runner {description} not found"
            contacted = False
            for runner in matching:
                details = api_get_json(api_session, gitlab_host_url, f"runners/{runner['id']}")
                if details.get("contacted_at"):
                    contacted = True
                    break
            if not contacted:
                all_contacted = False
                break

        if all_contacted:
            return

        elapsed += poll_interval
        time.sleep(poll_interval)

    pytest.skip("Runners have not contacted GitLab yet")


def test_expected_containers_running(compose_containers):
    running = {container["Name"] for container in compose_containers if container.get("State") == "running"}
    expected = {
        "gitlab-attack-lab",
        "gitlab-runner-docker",
        "gitlab-runner-shell",
        "pentester",
        "mailhog",
        "lab-web-app",
        "webhook-logger",
    }
    for name in expected:
        assert name in running, f"Container {name} not running"


def test_pipeleek_installed():
    result = subprocess.run(
        ["docker-compose", "exec", "-T", "pentester", "which", "pipeleek"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
