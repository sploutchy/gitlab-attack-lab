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
make pentester-shell
```

Inside the container, edit the pipeleek config file with vim and add your token:

```bash
# Open the config file in vim
vim ~/.config/pipeleek/pipeleek.yaml

# In vim, find the line with "token:" and replace <your-token-from-step-3> with your actual token
# The file should look like:
# gitlab:
#   url: http://gitlab
#   token: <your-token-from-step-3>
```

# Now use pipeleek to enumerate GitLab
```bash
# Enumerate users, groups, projects
pipeleek enum
# Enumerate accessible runners            
pipeleek runners               

# Or use the GitLab API directly with curl
GITLAB_TOKEN=<your-token-from-step-3>
curl -H "PRIVATE-TOKEN: $GITLAB_TOKEN" http://gitlab/api/v4/projects | jq
```

##  Stop the Lab

```bash
make stop               # Stop containers
make destroy            # Stop and remove all data
```

## 📝 Notes

- Setup is idempotent (safe to re-run)
- GitLab runs at `http://127.0.0.1`
- Default root password: `R00t@L4b_Adm1n_2024`
- All services run in Docker containers
- Data persists in Docker volumes (use `-v` flag to remove)
