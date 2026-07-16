---
id: scenario-00-getting-started
title: Getting Started with GitLab Attack Lab
difficulty: beginner
order: 0
flags:
  - name: Welcome Flag
    pattern: "^flag\\{welcome_[a-z0-9]{16}\\}$"
solution:
  title: Solution
  content: |
    1. Navigate to the **security-tools** project
    2. Open the CI/CD → Pipelines section
    3. Click on any recent pipeline to view job logs
    4. Look for the `scan` job that echoes the welcome flag
    5. Copy the flag in the format `flag{welcome_XXXXXXXXXXXXXXXX}`
    6. Submit the flag in the lab's flag submission interface
hints:
  - title: Basic Hint
    content: Check the **security-tools** project's CI/CD logs for the flag.
  - title: Advanced Hint
    content: Look for printenv command in the pipeline jobs.
---

## Objective

Learn how to use the GitLab Attack Lab and submit your first flag.

## Background

GitLab Attack Lab is an interactive learning platform for understanding GitLab CI/CD security misconfiguration.

## Scenario Description

1. Open your browser and navigate the GitLab login mask http://127.0.0.1:7700
2. Login with credential `pentester` and `SecureP3nt3st3r@2024!`
3. Look at the projects your user has access to e.g. is a member of
4. The first flag follows this pattern: `flag{welcome_XXXXXXXXXXXXXXXX}`

## Tooling Setup

Several later scenarios use [Pipeleek](https://github.com/CompassSecurity/pipeleek), pre-installed in the pentester container. Set it up now so it's ready when you need it:

1. Start the pentester container: `make shell`
2. Create a new Personal Access Token in the GitLab UI:
   - Go to http://localhost:7700 > User Settings > Access > Personal Access Tokens
   - Set the Scopes: api, read_api, read_repository
3. Add the created token under the `token` key in the Pipeleek config file `~/.config/pipeleek/pipeleek.yaml`:

```bash
# edit the config file
vim ~/.config/pipeleek/pipeleek.yaml

# Modify the content and add the PAT you've generated before
gitlab:
  url: http://gitlab
  token: glpat-3qXyv3VI_nWJ8uin5ucy6m86MQp1OjIH.01.[example]

# Test it's working
pipeleek enum
```
