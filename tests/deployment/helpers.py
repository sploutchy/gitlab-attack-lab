"""
Shared helpers for deployment validation tests.
"""

from __future__ import annotations

from pathlib import Path
import os
import subprocess

import requests
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_env_file() -> dict[str, str]:
    env_values: dict[str, str] = {}
    env_path = PROJECT_ROOT / ".env"

    if not env_path.exists():
        return env_values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_values[key] = value

    return env_values


def env_value(name: str, default: str | None = None) -> str | None:
    if name in os.environ and os.environ[name]:
        return os.environ[name]
    return load_env_file().get(name, default)


def merged_config() -> dict:
    merged_output = Path("/tmp/gitlab-lab-merged-deployment.yml")
    result = subprocess.run(
        [
            "python3",
            str(PROJECT_ROOT / "scripts" / "merge-scenarios.py"),
            "--base",
            str(PROJECT_ROOT / "lab-config" / "base.yml"),
            "--scenarios",
            str(PROJECT_ROOT / "lab-config" / "scenarios"),
            "--output",
            str(merged_output),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    with open(merged_output, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def api_get_json(session: requests.Session, gitlab_url: str, endpoint: str, **kwargs):
    response = session.get(f"{gitlab_url}/api/v4/{endpoint}", **kwargs)
    response.raise_for_status()
    return response.json()


def find_user(session: requests.Session, gitlab_url: str, username: str) -> dict:
    users = api_get_json(session, gitlab_url, "users", params={"username": username})
    for user in users:
        if user["username"] == username:
            return user
    raise AssertionError(f"User '{username}' not found")


def find_group(session: requests.Session, gitlab_url: str, group_path: str) -> dict:
    groups = api_get_json(session, gitlab_url, "groups", params={"search": group_path})
    for group in groups:
        if group["path"] == group_path:
            return group
    raise AssertionError(f"Group '{group_path}' not found")


def find_project(session: requests.Session, gitlab_url: str, path_with_namespace: str) -> dict:
    search_term = path_with_namespace.split("/")[-1]
    projects = api_get_json(
        session,
        gitlab_url,
        "projects",
        params={"search": search_term, "membership": False, "per_page": 100},
    )
    for project in projects:
        if project["path_with_namespace"] == path_with_namespace:
            return project
    raise AssertionError(f"Project '{path_with_namespace}' not found")


def get_project_variable(session: requests.Session, gitlab_url: str, project_id: int, key: str) -> dict:
    variables = api_get_json(session, gitlab_url, f"projects/{project_id}/variables")
    for variable in variables:
        if variable["key"] == key:
            return variable
    raise AssertionError(f"Variable '{key}' not found in project {project_id}")


def get_project_members(session: requests.Session, gitlab_url: str, project_id: int) -> list[dict]:
    return api_get_json(session, gitlab_url, f"projects/{project_id}/members")


def get_project_schedules(session: requests.Session, gitlab_url: str, project_id: int) -> list[dict]:
    return api_get_json(session, gitlab_url, f"projects/{project_id}/pipeline_schedules")
