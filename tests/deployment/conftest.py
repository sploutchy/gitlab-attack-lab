"""
Pytest fixtures for deployment validation tests.
"""

from __future__ import annotations

import subprocess

import pytest
import requests

from .helpers import env_value, merged_config


pytestmark = pytest.mark.deployment


@pytest.fixture(scope="session")
def gitlab_host_url() -> str:
    return (env_value("GITLAB_HOST_URL", "http://127.0.0.1:7700") or "http://127.0.0.1:7700").rstrip("/")


@pytest.fixture(scope="session")
def admin_token() -> str:
    token = env_value("GITLAB_ADMIN_TOKEN")
    if not token:
        pytest.skip("GITLAB_ADMIN_TOKEN not found. Run 'make setup' first.")
    return token


@pytest.fixture(scope="session")
def ensure_gitlab_ready(gitlab_host_url: str):
    try:
        response = requests.get(f"{gitlab_host_url}/api/v4/version", timeout=10)
    except requests.RequestException as exc:
        pytest.skip(f"GitLab not reachable at {gitlab_host_url}: {exc}")

    if response.status_code not in {200, 401}:
        pytest.skip(f"GitLab not ready at {gitlab_host_url}: HTTP {response.status_code}")


@pytest.fixture(scope="session")
def api_session(ensure_gitlab_ready, admin_token: str):
    session = requests.Session()
    session.headers.update({"PRIVATE-TOKEN": admin_token, "Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def structure_config() -> dict:
    return merged_config()


@pytest.fixture(scope="session")
def compose_containers() -> list[dict]:
    result = subprocess.run(
        ["docker-compose", "ps", "--format", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip("docker-compose ps failed; deployment is not available")

    containers = []
    for line in result.stdout.strip().splitlines():
        if line:
            import json

            containers.append(json.loads(line))
    return containers
