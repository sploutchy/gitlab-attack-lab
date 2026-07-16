# GitLab Attack Lab 🏴‍☠️

A containerized GitLab pentesting lab for learning and practicing GitLab CI/CD security vulnerabilities with [Pipeleek](https://github.com/CompassSecurity/pipeleek).

## Prerequisites

- **Docker**, with the daemon running
- **Docker Compose v2** (the `docker compose` CLI plugin subcommand)

  `docker-compose.yml` uses a `develop:` key that is only supported by Compose v2. The older standalone `docker-compose` v1 binary cannot parse this file and will fail with `Unsupported config option for services.lab-web: 'develop'`. Verify with `docker compose version`; see the [Compose install docs](https://docs.docker.com/compose/install/) if it's missing.

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

Open your browser: `http://127.0.0.1:7700`

Login as:
- **Username:** `pentester`
- **Password:** `SecureP3nt3st3r@2024!`

### 3. Getting Started

Access the lab scenarios and descriptions and get started on http://localhost:7706

## System Requirements

This lab runs multiple heavy services (GitLab, runners, web app, pentester tooling).

- **CPU:** 4 vCPUs recommended (2 vCPUs minimum, but slower setup and job execution)
- **RAM:** 8 GB recommended (4 GB minimum, but GitLab may be unstable under load)
- **Disk Absolute minimum:** 20 GB free
