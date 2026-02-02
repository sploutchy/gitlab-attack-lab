"""
Pytest configuration for GitLab Attack Lab tests
"""

import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='session')
def gitlab_url():
    """GitLab URL fixture"""
    return os.getenv('GITLAB_URL', 'http://127.0.0.1')

@pytest.fixture(scope='session')
def admin_token():
    """Admin token fixture"""
    env_file = '.env'
    if not os.path.exists(env_file):
        pytest.fail(f"{env_file} not found")
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('GITLAB_ADMIN_TOKEN='):
                token = line.split('=', 1)[1].strip()
                if token:
                    return token
    
    pytest.fail("GITLAB_ADMIN_TOKEN not found in .env")

@pytest.fixture(scope='session')
def structure_config():
    """Load merged configuration from base + scenarios"""
    import yaml
    import subprocess
    
    base_config = 'lab-config/base.yml'
    scenarios_dir = 'lab-config/scenarios'
    merge_script = 'scripts/merge-scenarios.py'
    merged_output = '/tmp/gitlab-lab-merged-test.yml'
    
    if not os.path.exists(base_config):
        pytest.fail(f"{base_config} not found")
    if not os.path.exists(scenarios_dir):
        pytest.fail(f"{scenarios_dir} not found")
    if not os.path.exists(merge_script):
        pytest.fail(f"{merge_script} not found")
    
    result = subprocess.run(
        [
            'python3', merge_script,
            '--base', base_config,
            '--scenarios', scenarios_dir,
            '--output', merged_output
        ],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        pytest.fail(f"Failed to merge scenarios: {result.stderr}")
    
    with open(merged_output, 'r') as f:
        return yaml.safe_load(f)
