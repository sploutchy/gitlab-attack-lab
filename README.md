# GitLab Attack Lab 🏴‍☠️

A containerized GitLab pentesting lab for learning and practicing GitLab CI/CD security vulnerabilities.

## 🚀 Quick Start

### 1. Start the Lab

```bash
make setup
```

This will:
- Start all Docker containers
- Initialize GitLab
- Create users, groups, projects with CI/CD pipelines
- Register runners

**Time: 5-15 minutes (first run), 2-5 minutes (re-runs)**

### 2. Access GitLab Web UI

Open your browser: `http://127.0.0.1`

Login as:
- **Username:** `pentester`
- **Password:** `SecureP3nt3st3r@2024!`

### 3. Create a Personal Access Token

In GitLab:
1. Click your profile icon (top-right) → **Edit Profile**
2. Go to **Access Tokens** (left sidebar)
3. Click **Add new token**
4. Name: `pentester-token`, Scopes: Select all
5. Copy the token

### 4. Start Hacking in the Pentester Container

```bash
docker-compose exec -it pentester /bin/bash
```

Inside the container, use your token:

```bash
export GITLAB_TOKEN=<your-token-from-step-3>
export GITLAB_URL=http://gitlab

# Use pipeleek to enumerate GitLab
pipeleek gl enum         # Enumerate users, groups, projects
pipeleek gl project-vars # Find exposed variables

# Or use the GitLab API directly
curl -H "PRIVATE-TOKEN: $GITLAB_TOKEN" http://gitlab/api/v4/projects | jq
curl -H "PRIVATE-TOKEN: $GITLAB_TOKEN" http://gitlab/api/v4/projects/1/variables | jq
```

## 📚 Scenarios

Available scenarios:
- **default.yml** - Multiple projects with exposed variables
- **scenario-1.yml** - Public CI/CD with exposed AWS credentials

Run a specific scenario:
```bash
SCENARIOS="lab-config/scenarios/scenario-1.yml" make setup
```

## 🛑 Stop the Lab

```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop and remove all data
```

## 📝 Notes

- Setup is idempotent (safe to re-run)
- GitLab runs at `http://127.0.0.1`
- Default root password: `R00t@L4b_Adm1n_2024`
- All services run in Docker containers
- Data persists in Docker volumes (use `-v` flag to remove)
