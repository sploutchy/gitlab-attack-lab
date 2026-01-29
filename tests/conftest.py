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
    """Load structure.yml configuration"""
    import yaml
    config_path = 'lab-config/structure.yml'
    
    if not os.path.exists(config_path):
        pytest.fail(f"{config_path} not found")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
