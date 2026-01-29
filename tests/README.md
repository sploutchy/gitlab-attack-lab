# GitLab Attack Lab - Test Suite

This directory contains the comprehensive test suite for validating the GitLab Attack Lab setup.

## Test Structure

### `test_integration.py`
Standalone integration test script that can be run independently:
```bash
python tests/test_integration.py
```

Tests:
- GitLab health and authentication
- User creation
- Group creation and memberships
- Project creation
- Repository imports
- CI/CD variables
- CI configurations
- Runner registration
- Runner online status
- Container status
- Pipeleek configuration

### `test_pytest.py`
Pytest-based test suite for use in CI/CD pipelines:
```bash
pytest tests/ -v
```

Organized into test classes:
- `TestGitLabHealth`: API health and authentication
- `TestUsers`: User creation validation
- `TestGroups`: Group and membership validation
- `TestProjects`: Project creation and repository imports
- `TestCICD`: CI/CD variables and configurations
- `TestRunners`: Runner registration and status
- `TestContainers`: Docker container status
- `TestPentesterTools`: Pentester container tools

### `conftest.py`
Pytest configuration and fixtures:
- `gitlab_url`: GitLab URL fixture
- `admin_token`: Admin token from .env
- `structure_config`: Loaded structure.yml configuration

## Running Tests

### Locally
```bash
# Run standalone integration tests
python tests/test_integration.py

# Run pytest suite
pytest tests/ -v

# Run with timeout
pytest tests/ -v --timeout=300

# Run specific test class
pytest tests/test_pytest.py::TestRunners -v
```

### In CI/CD
Tests run automatically in GitHub Actions on:
- Push to main or develop branches
- Pull requests to main
- Manual workflow dispatch

See `.github/workflows/test.yml` for CI configuration.

## Test Requirements

Python packages (installed in CI):
- requests
- pyyaml
- pytest
- pytest-timeout

The tests expect:
- GitLab running at http://127.0.0.1
- .env file with GITLAB_ADMIN_TOKEN
- lab-config/structure.yml configuration file
- All containers running via docker-compose

## Test Coverage

✅ **Infrastructure**
- GitLab container health
- All required containers running
- GitLab API responding

✅ **Authentication**
- Admin token working
- Admin privileges verified

✅ **Users & Groups**
- All users created
- All groups created
- Group memberships correct

✅ **Projects**
- All projects created
- Projects in correct groups
- Repositories imported with content

✅ **CI/CD**
- Variables created
- Variables properly protected/masked
- .gitlab-ci.yml files present

✅ **Runners**
- Runners registered
- Runners contacted GitLab
- Runners available for jobs

✅ **Tools**
- Pipeleek installed
- Pipeleek configured
- Pentester container ready

## Troubleshooting

**Test fails: "GitLab not responding"**
- Wait for GitLab to finish initializing (3-5 minutes)
- Check: `docker-compose logs gitlab`

**Test fails: "Runner hasn't contacted"**
- Runners may need 15-30 seconds to register and contact
- Check: `docker logs gitlab-runner-docker`

**Test fails: "Admin token not found"**
- Run `make setup` first to generate .env with token
- Check: `cat .env | grep GITLAB_ADMIN_TOKEN`

**Test fails: "Container not running"**
- Check all containers: `docker-compose ps`
- Restart: `docker-compose up -d`
