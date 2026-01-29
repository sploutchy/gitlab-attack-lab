# GitLab Attack Lab 🏴‍☠️

A fully functional GitLab CI/CD security research and pentesting lab environment with integrated security scanning tools.

## 🎯 What is This?

GitLab Attack Lab is a containerized environment designed for security researchers and pentesters to:
- **Learn** about GitLab CI/CD security risks
- **Test** security scanning tools like Pipeleek
- **Demonstrate** real-world CI/CD vulnerability scenarios
- **Practice** GitLab-focused penetration testing

The lab simulates a realistic organization with multiple projects, CI/CD pipelines, environment variables, and secrets - perfect for hands-on security research.

## 🚀 Quick Start

### One-Command Setup

Run this single command to set up everything - services, data, and a pentester shell:

```bash
make setup
```

That's it! The command will:
- ✅ Start Docker containers
- ✅ Wait for GitLab to initialize
- ✅ Apply all configuration from YAML
- ✅ Open a shell in the pentester container (with pre-configured credentials)

**Estimated time: 5-10 minutes**

### Manual Step-by-Step Setup

If you prefer to run steps manually:

```bash
# Step 1: Start services
make start

# Step 2: Initialize GitLab (wait for healthy status)
make init

# Step 3: Apply configuration
make config

# Step 4: Enter pentester container
make pentester-shell
```

## 📖 Playing Through the Lab

### Phase 1: Access GitLab Web Interface

```bash
# Open your browser
http://127.0.0.1

# Login with:
Username: root
Password: R00t@L4b_Adm1n_2024
```

**What to explore:**
- Navigate to **Projects** → See all 5 projects
- Click on **web-app** → View the `.gitlab-ci.yml` pipeline
- Go to **Settings** → **CI/CD** → **Variables** → See exposed environment variables
- Check **Members** to see users and their access levels
- Explore **Groups** and see how security-team, devops-team, and development-team are organized

### Phase 2: Access the Pentester Container

Open a shell inside the pentester container with all tools pre-configured:

```bash
docker-compose exec pentester /bin/bash
```

Inside the container, you have:
- **Pipeleek** v0.52.0 - GitLab CI/CD security scanner
- **curl** - For manual API testing
- **jq** - JSON processing

### Phase 3: Scan with Pipeleek

Pipeleek is a specialized tool for discovering secrets and sensitive data in GitLab. Try these commands:

#### Command 1: Enumerate All Resources
```bash
pipeleek gl enum --gitlab http://gitlab --token glpat-attack-lab-admin-token-2024
```

**What it finds:**
- Administrator user with full privileges
- Access tokens and their scopes
- All 3 groups (security-team, devops-team, development-team)
- All 5 projects
- Project access levels

**Key findings:**
```
Current user admin=true username=root
Current Token scopes=api,read_user,read_api,read_repository,write_repository,sudo
Found Group: "Security Team" (private)
Found Group: "DevOps Team" (private)  
Found Group: "Development Team" (private)
Found Project: "web-app"
Found Project: "api-service"
Found Project: "mobile-app"
Found Project: "infrastructure"
Found Project: "security-tools"
```

#### Command 2: Extract CI/CD Variables
```bash
pipeleek gl variables --gitlab http://gitlab --token glpat-attack-lab-admin-token-2024
```

**What it discovers:**
- All environment variables from every project
- Protected/sensitive variables (even though marked as "protected")
- Values and security settings
- Variable visibility and scope

**Example variables found:**
```
DEPLOY_ENV=production
DEPLOY_TOKEN=deploy-token-abc123xyz (⚠️ marked protected but readable!)
TEST_DB_HOST=db.lab.local
REGISTRY_URL=registry.lab.local
```

**Security insight:** Even "protected" variables are enumerable via API if you have valid authentication!

#### Command 3: Scan for Secrets in Pipelines
```bash
pipeleek gl scan --gitlab http://gitlab --token glpat-attack-lab-admin-token-2024
```

**What it does:**
- Scans all projects and their repositories
- Analyzes CI/CD pipeline history
- Searches for exposed secrets in logs
- Identifies potentially sensitive information

#### Command 4: Enumerate Runners
```bash
pipeleek gl runners --gitlab http://gitlab --token glpat-attack-lab-admin-token-2024
```

**What it reveals:**
- Registered CI/CD runners
- Runner capabilities and limits
- Executor types (Docker, Shell)
- Runner tokens and authentication

### Phase 4: Manual API Testing

Exit Pipeleek and test the GitLab API directly:

```bash
# From pentester container or host
TOKEN="glpat-attack-lab-admin-token-2024"

# Get version info
curl -H "PRIVATE-TOKEN: $TOKEN" http://gitlab/api/v4/version | jq

# List all projects
curl -H "PRIVATE-TOKEN: $TOKEN" http://gitlab/api/v4/projects | jq

# List variables in a project (ID 1 = web-app)
curl -H "PRIVATE-TOKEN: $TOKEN" http://gitlab/api/v4/projects/1/variables | jq

# Get runner info
curl -H "PRIVATE-TOKEN: $TOKEN" http://gitlab/api/v4/runners | jq
```

## 🎓 Learning Scenarios

### Scenario 1: Discover Infrastructure Details
**Goal:** Find internal hostnames and infrastructure info from variables

```bash
# Use Pipeleek to extract all variables
pipeleek gl variables --gitlab http://gitlab --token glpat-attack-lab-admin-token-2024

# Notice:
# - TEST_DB_HOST=db.lab.local (reveals database location)
# - REGISTRY_URL=registry.lab.local (reveals registry location)
```

### Scenario 2: Identify Sensitive Tokens
**Goal:** Find and extract authentication tokens

```bash
pipeleek gl variables --gitlab http://gitlab --token glpat-attack-lab-admin-token-2024 | grep -i "token\|key\|secret"

# Notice:
# - DEPLOY_TOKEN marked as "protected" but still readable
# - Shows why access control matters in CI/CD
```

### Scenario 3: Map User Privileges
**Goal:** Understand user roles and access levels

```bash
# Enumerate to see all users and groups
pipeleek gl enum --gitlab http://gitlab --token glpat-attack-lab-admin-token-2024

# Observe:
# - root is admin with full access (accessLevel=50)
# - Other users have varying permissions
# - Shows importance of least privilege principle
```

### Scenario 4: Analyze Pipeline Exposure
**Goal:** Examine what information is exposed in CI/CD configurations

```bash
# Look at a project's pipeline
curl -H "PRIVATE-TOKEN: glpat-attack-lab-admin-token-2024" \
  http://gitlab/api/v4/projects/1/repository/files/.gitlab-ci.yml?ref=main | jq

# Notice:
# - Pipelines reference environment variables
# - Variables are injected at runtime
# - Logs capture variable values (security risk!)
```

## 🔧 Advanced Usage

### Declarative YAML Configuration

The lab uses a declarative YAML-based approach to define all GitLab data. The configuration file is at `lab-config/structure.yml` and defines:

- Users (with credentials and access levels)
- Groups (with visibility settings)
- Projects (with descriptions)
- CI/CD Variables (with protection and masking settings)

#### Customizing the Lab

Edit `lab-config/structure.yml` to:
- Add/remove users, groups, or projects
- Modify variable values
- Change pipeline configurations
- Adjust visibility and access levels

Then apply changes:
```bash
make config
```

#### Example: Add a New User

Edit `lab-config/structure.yml`:
```yaml
users:
  - username: newuser
    email: newuser@lab.local
    name: "New User"
    password: "SecurePass2024!"
    access_level: 30  # Developer
```

Then apply:
```bash
make config
```

### Use Localhost Instead of Hostname
If commands fail with hostname resolution errors, use localhost:

```bash
pipeleek gl enum --gitlab http://127.0.0.1 --token glpat-attack-lab-admin-token-2024
```

### Test Different User Permissions
Create tokens for different users and test what they can access:

```bash
# Inside pentester container
# Try enumerating with alice's token (if you create one)
pipeleek gl enum --gitlab http://gitlab --token alice-token-here
```

### Access GitLab CLI
Test GitLab's CLI tool if interested:

```bash
docker-compose exec pentester bash
# Try: glab --help
# Note: You may need to configure glab with your token
```

### View Real Logs
See actual pipeline execution logs:

```bash
# Access GitLab web UI → Projects → web-app → CI/CD → Pipelines
# Click on a pipeline to see the build logs
```

## 📊 Lab Contents

### Users (4 total)
| User | Password | Role |
|------|----------|------|
| root | R00t@L4b_Adm1n_2024 | Administrator |
| alice | SecurePass2024! | Developer |
| bob | SecurePass2024! | Maintainer |
| charlie | SecurePass2024! | Guest |
| pentester | Pentester@123 | Developer |

### Projects (5 total)
| Project | Description | Variables |
|---------|-------------|-----------|
| web-app | Main web application | DEPLOY_ENV, DEPLOY_TOKEN, TEST_DB_HOST, REGISTRY_URL |
| api-service | REST API | DEPLOY_ENV, DEPLOY_TOKEN, TEST_DB_HOST, REGISTRY_URL |
| mobile-app | Mobile app | DEPLOY_ENV, DEPLOY_TOKEN, TEST_DB_HOST, REGISTRY_URL |
````
| infrastructure | Infrastructure code | DEPLOY_ENV, DEPLOY_TOKEN, TEST_DB_HOST, REGISTRY_URL |
| security-tools | Security tools | DEPLOY_ENV, DEPLOY_TOKEN, TEST_DB_HOST, REGISTRY_URL |

### Groups (3 total)
- security-team
- devops-team
- development-team

### Exposed Secrets

| Secret | Type | Finding |
|--------|------|---------|
| DEPLOY_TOKEN | Protected Variable | Marked protected but readable via API |
| ROOT_PASSWORD | Implicit | GitLabLab2024! (default credentials) |
| Test DB Location | Infrastructure Info | db.lab.local (information disclosure) |
| Registry URL | Infrastructure Info | registry.lab.local (network mapping) |

## 🛠️ Useful Commands

```bash
# Check if services are running
docker-compose ps

# View GitLab logs
docker-compose logs gitlab | tail -50

# Restart a service
docker-compose restart gitlab

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v

# Open pentester shell
docker-compose exec pentester /bin/bash

# View token from .env
grep PENTESTER_TOKEN .env

# Test GitLab health
curl -v http://127.0.0.1/api/v4/version

# Check if specific project exists
curl -H "PRIVATE-TOKEN: glpat-attack-lab-admin-token-2024" \
  http://127.0.0.1/api/v4/projects | jq '.[] | .name'
```

## 📚 Additional Resources

- **TEST_RESULTS.md** - Complete test report with security findings
- **docs/USAGE.md** - Detailed usage guide (if present)
- **GitLab API Docs** - https://docs.gitlab.com/ee/api/
- **Pipeleek GitHub** - https://github.com/fitzy101/pipeleek

## ⚠️ Important Security Notes

🔴 **THIS IS A LAB ENVIRONMENT ONLY**

- Default credentials are intentionally weak
- Secrets are exposed by design for learning
- No security hardening is applied
- Should never be exposed to the internet
- Not suitable for production use
- Do not use with real GitLab instances

✅ **Suitable for:**
- Security research and learning
- Penetration testing practice
- Tool evaluation and testing
- CI/CD vulnerability research
- Red team exercises
- Educational demonstrations

## 🧹 Cleanup & Restart

### Stop Services (Keep Data)
Pause the lab but preserve all data:

```bash
docker-compose down
# Services stop, volumes preserved
# Restart anytime with: docker-compose up -d
```

### Complete Cleanup (Destroy Everything)
Completely remove all lab data and start fresh:

```bash
# Option 1: Remove containers and volumes
docker-compose down -v

# Option 2: Manual cleanup (more control)
docker-compose down
docker volume rm gitlab_config gitlab_data gitlab_logs gitlab_runner_docker_config gitlab_runner_docker_builds gitlab_runner_docker_cache gitlab_runner_shell_config gitlab_runner_shell_builds gitlab_runner_shell_cache

# Option 3: Total nuclear option (also removes images)
docker-compose down -v
docker rmi gitlab/gitlab-ce:latest
docker rmi gitlab/gitlab-runner:latest
```

### Restart After Cleanup

After destroying the lab, restart it fresh:

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait 3-5 minutes for GitLab to initialize
# (Watch progress with: docker-compose logs -f gitlab)

# 3. Test that GitLab is ready
curl http://127.0.0.1/api/v4/version

# 4. Everything is auto-populated! You're ready to go
# Login with:
# Username: root
# Password: R00t@L4b_Adm1n_2024
```

### Verify Cleanup
Check what's left after cleanup:

```bash
# View all Docker volumes
docker volume ls | grep gitlab

# View all Docker images
docker images | grep gitlab

# View running containers
docker-compose ps
```

## ❓ Troubleshooting

### "Connection refused" errors
The GitLab container is still initializing. Wait 2-3 minutes and try again.

### Pipeleek commands fail with hostname error
Use `http://127.0.0.1` instead of `http://gitlab`:
```bash
pipeleek gl enum --gitlab http://127.0.0.1 --token glpat-attack-lab-admin-token-2024
```

### Can't access GitLab web interface
Check if services are running: `docker-compose ps`  
Check logs: `docker-compose logs gitlab | tail -20`

### Port 80 already in use
The lab uses port 80 (HTTP). If you have another service using it, stop that service or modify docker-compose.yml to use a different port.

## 📝 License

This lab environment is provided as-is for educational and authorized security testing purposes.

---

**Ready to learn?** Start with Phase 1, work through each scenario, and explore the security implications of CI/CD misconfigurations!
3. ✅ Created 6 groups with proper hierarchy
4. ✅ Created 15+ test projects across different categories
5. ✅ Added 5 vulnerable CI/CD pipelines
6. ✅ Populated 25+ CI/CD variables with fake secrets
7. ✅ Uploaded 4 secure files (SSH keys, kubeconfig, etc.)
8. ✅ Created 2 pipeline schedules
9. ✅ Configured pentester container with GitLab token
10. ✅ Triggered initial pipeline runs

## Manual Setup (Step-by-Step)

If you prefer to run each phase manually:

### 1. Clone or Navigate to Repository

```bash
cd /workspaces/gitlab-attack-lab
```

### 2. Configure Environment

```bash
# Copy example configuration (if not already present)
cp .env.example .env

# Edit .env to customize (optional)
nano .env
```

### 1. Start Services

```bash
docker-compose up -d
# OR
make start
```

### 2. Initialize GitLab

```bash
bash scripts/init-gitlab.sh
# OR
make init
```

### 3. Setup Users and Groups

```bash
bash scripts/setup-gitlab.sh
# OR
make setup
```

### 4. Create Test Projects

```bash
bash scripts/create-projects.sh
# OR
make projects
```

### 5. Add CI/CD Pipelines

```bash
bash scripts/create-pipelines.sh
# OR
make pipelines
```

### 6. Populate Variables and Secrets

```bash
bash scripts/populate-variables.sh
# OR
make populate
```

### 7. Setup Pentester Container

```bash
bash scripts/setup-pentester.sh
# OR
make pentester
```

## Using the Pentester Container

The pentester container has pipeleek pre-installed and pre-configured with your GitLab instance.

### Enter Pentester Shell

```bash
make pentester-shell
```

### Run Pipeleek Tests

Once inside the container:

```bash
# Run all tests
./test-pipeleek.sh

# Or run individual commands
pipeleek gitlab enum                          # List all projects
pipeleek gitlab scan --group security-lab     # Scan for secrets
pipeleek gitlab variables --project web-app   # List variables
pipeleek gitlab secureFiles --project infra   # List secure files
pipeleek gitlab runners                       # List runners
pipeleek gitlab schedule --group security-lab # List schedules
```

### Pipeleek Configuration

The config file is pre-configured at `~/.config/pipeleek/pipeleek.yaml`:

```yaml
gitlab:
  url: "http://gitlab"
  token: "glpat-xxxxxxxxxxxxxxxxxxxxx"  # Auto-generated
```

## Access GitLab Web UI

Once initialization is complete:

- **URL**: http://localhost (or http://gitlab.local if using host entry)
- **Username**: `root`
- **Password**: From `.env` file (default: `GitLabLab2024!`)

## Default Test Users

| Username | Email | Password | Role |
|----------|-------|----------|------|
| root | root@localhost | *from .env* | Admin |
| alice | alice@lab.local | testpass123 | Developer |
| bob | bob@lab.local | testpass123 | Maintainer |
| charlie | charlie@lab.local | testpass123 | Owner |
| dave | dave@lab.local | testpass123 | Guest |
| eve | eve@lab.local | testpass123 | Reporter |
| pentester | pentester@lab.local | *auto-generated token* | Security Tester |

## Test Data Overview

### Groups
- `security-lab` (main group)
  - `web-projects`
    - `frontend-team`
    - `backend-team`
  - `mobile-projects`
  - `infrastructure`
  - `legacy-systems`

### Projects (15+)
- Web applications with vulnerable pipelines
- Mobile app projects with keystore credentials
- Infrastructure as code with cloud provider tokens
- Docker image builds with registry credentials
- Data pipelines with database credentials

### CI/CD Variables (25+)
- AWS access keys and secrets
- Database URLs (PostgreSQL, MySQL, MongoDB)
- API tokens (Stripe, SendGrid, Twilio, GitHub, NPM)
- Cloud provider tokens (DigitalOcean, Datadog, Terraform Cloud)
- JWT secrets and encryption keys

### Secure Files (4)
- SSH private keys
- Kubernetes config files
- GCP service account JSON
- SSL certificates

### Pipeline Schedules (2)
- Daily backup job (2 AM)
- Nightly builds (midnight)

## Project Structure

```
gitlab-attack-lab/
├── setup.sh                    # One-command setup script
├── docker-compose.yml          # Service definitions
├── .env                        # Configuration
├── .env.example                # Example configuration
├── lab-config/
│   └── structure.yml           # Declarative lab definition
├── scripts/
│   └── populate-gitlab.py       # Populator script
├── pentester/
│   ├── Dockerfile               # Pentester image
│   ├── config/                  # Pentester config files
│   └── workspace/               # Pentester workspace
├── README.md                   # Main documentation
├── DECLARATIVE_CONFIG.md        # Config reference
├── IMPLEMENTATION_SUMMARY.md    # Implementation notes
└── LICENSE
```

## Available Commands

### Setup Commands
```bash
make start          # Start all services
make init           # Initialize GitLab
make setup          # Create users/groups
make projects       # Create test projects
make pipelines      # Add CI/CD pipelines
make populate       # Add variables/secrets
make pentester      # Setup pentester container
make full-setup     # Run everything
```

### Testing Commands
```bash
make test           # Run pipeleek tests
make pentester-shell # Enter pentester container
```

### Management Commands
```bash
make status         # Show container status
make logs           # Show GitLab logs
make runner-logs    # Show runner logs
make shell          # Enter GitLab container
make restart        # Restart all services
make stop           # Stop all services
make clean          # Delete everything (WARNING!)
```

# Enumerate access rights
pipeleek gl enum --token glpat-xxxxx --gitlab http://localhost
```

## Accessing Services

| Service | URL | Port |
|---------|-----|------|
| GitLab Web UI | http://localhost | 80 |
| GitLab SSH | localhost | 22 |
| GitLab API | http://localhost/api/v4 | 80 |
| MailHog | http://localhost:8025 | 8025 |
| MailHog SMTP | localhost | 1025 |

## Useful Commands

```bash
# View container logs
docker-compose logs gitlab
docker-compose logs gitlab-runner-docker
docker-compose logs gitlab-runner-shell

# Enter GitLab container
docker-compose exec gitlab /bin/bash

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Remove all volumes (WARNING: deletes all data)
docker-compose down -v

# Get runner registration token (from logs)
docker-compose logs gitlab | grep "Runner registration token"
```

## Troubleshooting

### GitLab Slow to Start

GitLab can take 2-5 minutes to fully initialize. Watch logs:

```bash
docker-compose logs -f gitlab | grep "unicorn"
```

### Cannot Connect to GitLab

1. Verify container is running: `docker-compose ps`
2. Check health: `docker-compose logs gitlab`
3. Wait longer and try again
4. Check port conflicts: `lsof -i :80`

### Runner Registration Issues

1. Get current token: `docker-compose exec gitlab grep "registration_token" /var/log/gitlab/gitlab-rails/production.log`
2. Update `.env` with correct token
3. Restart runners: `docker-compose restart gitlab-runner-docker gitlab-runner-shell`

### API Authentication Fails

1. Verify root password in `.env`
2. Check GitLab is healthy: `curl http://localhost/-/health`
3. Try authenticating manually: `curl -X POST http://localhost/api/v4/session -d "username=root&password=..."`

## Performance Tuning

If running into resource constraints, adjust in `docker-compose.yml`:

```yaml
gitlab:
  environment:
    GITLAB_OMNIBUS_CONFIG: |
      puma['worker_processes'] = 2        # Reduce from default
      postgresql['max_connections'] = 100 # Reduce from default
      redis['maxmemory'] = '256mb'       # Reduce from default
```

Then restart: `docker-compose down && docker-compose up -d`

## Security Notes

⚠️ **This lab contains intentionally vulnerable configurations and hardcoded secrets for testing purposes only.**

- Do NOT expose this lab to untrusted networks
- Use unique, strong passwords in production
- Change default credentials before using in shared environments
- Lab data contains fake but realistic secrets - never use real credentials
- Regularly clean up old pipelines and artifacts to save space

## Documentation

- [PLAN.md](PLAN.md) - Full project plan and design
- [docs/USAGE.md](docs/USAGE.md) - Detailed usage guide
- [docs/TESTING.md](docs/TESTING.md) - Testing procedures
- [docs/pipeleek-commands.md](docs/pipeleek-commands.md) - Pipeleek command reference

## Support & Issues

For issues or improvements:
1. Check troubleshooting section above
2. Review GitLab logs: `docker-compose logs gitlab`
3. Verify .env configuration
4. Try clean restart: `docker-compose down && docker-compose up -d`

## License

See [LICENSE](LICENSE) file for details.
