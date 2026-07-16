# GitLab Attack Lab 🏴‍☠️

A containerized GitLab pentesting lab for learning and practicing GitLab CI/CD security vulnerabilities with [Pipeleek](https://github.com/CompassSecurity/pipeleek).

## Prerequisites

- **Docker**, with the daemon running
- **`docker-compose`** (the standalone v1 binary) available on your `PATH`

  This lab's `Makefile` and `setup.sh` invoke `docker-compose` directly rather than the newer `docker compose` v2 CLI plugin subcommand. If your system only has Compose v2 (i.e. `docker compose version` works but `docker-compose version` does not), install the standalone [`docker-compose`](https://docs.docker.com/compose/install/standalone/) binary before running `make setup`.

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
