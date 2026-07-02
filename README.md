# GitLab Attack Lab 🏴‍☠️

A containerized GitLab pentesting lab for learning and practicing GitLab CI/CD security vulnerabilities with [Pipeleek](https://github.com/CompassSecurity/pipeleek).

## 🚀 Quick Start

### 1. Start the Lab

```bash
make setup
```

This will:
- Pre-pull common CI runner images once (with retries)
- Start all Docker containers
- Initialize GitLab
- Create users, groups, projects with CI/CD pipelines
- Register runners

**Time: 5-15 minutes**

### 2. Access GitLab Web UI

Open your browser: `http://127.0.0.1:8081`

Login as:
- **Username:** `pentester`
- **Password:** `SecureP3nt3st3r@2024!`

### 3. Getting Started

Access the lab scenarios and descriptions and get started on http://localhost:8080

## Testing

- CI-safe tests: `make test-ci`
- Full deployment validation: `make setup` or `make test-deployment`

The CI-safe suite validates Python and bash scripts, YAML/config structure, merge logic,
and template validation without requiring a live GitLab instance. The deployment suite
targets the provisioned lab state, including global configuration and each scenario.

## System Requirements

This lab runs multiple heavy services (GitLab, runners, web app, pentester tooling).

- **CPU:** 4 vCPUs recommended (2 vCPUs minimum, but slower setup and job execution)
- **RAM:** 8 GB recommended (4 GB minimum, but GitLab may be unstable under load)
- **Disk Absolute minimum:** 20 GB free
