---
id: scenario-01-cicd-variables-exposure
title: CI/CD Variables Exposure
difficulty: beginner
order: 2
flags:
  - name: Variables Leak Flag
    pattern: "^flag\\{cicd_vars_[a-z0-9]{16}\\}$"
solution:
  title: Solution
  content: |
    1. Start the pentester container: `make lab-pentester-shell`
    2. Export your GitLab token: `export GITLAB_TOKEN="<your-pat>"`
    3. Use pipeleek to scan for variable leaks: `pipeleek --gitlab-url http://gitlab:80 scan`
    4. Review the web-app or api-service project pipelines
    5. Look for jobs that echo environment variables or use verbose logging
    6. Extract the flag from the pipeline job logs
    7. Submit the flag: `flag{cicd_vars_XXXXXXXXXXXXXXXX}`
hints:
  - title: Basic Hint
    content: Look for jobs that echo environment variables or use `printenv` in the pipeline logs.
  - title: Intermediate Hint
    content: Check the **web-app** or **api-service** project pipelines for scripts that print secrets.
  - title: Advanced Hint
    content: Search for masked variables that are accidentally logged through debugging flags or verbose output.
---

# CI/CD Variables Exposure

## Objective
Identify how CI/CD variables can be exposed in pipeline logs and artifacts and extract the flag.

## Background
Many teams store secrets as CI/CD variables. Misconfigured jobs or verbose logging can leak these values.

## Steps to Complete This Scenario

**Access the GitLab Instance**


**Start the Pentester Container**
- From the lab root, run: `make lab-pentester-shell`
- This opens a shell in the pentester container.

**Configure Your Pentester PAT**
- In the pentester shell, export your token so tooling can authenticate:
  - `export GITLAB_TOKEN="<your-personal-access-token>"`
- Verify access with a quick API call:
  - `curl -s "$GITLAB_URL/api/v4/projects" | head -n 5`

**Explore Manually and with Pipeleek**
- Start by reviewing CI/CD pipelines in the GitLab UI.
- Then use pipeleek inside the pentester container to enumerate and detect variable leaks.

**Extract the Flag**
- Find the flag in the logs. It follows: `flag{cicd_vars_XXXXXXXXXXXXXXXX}`

## Summary
By completing this scenario, you'll learn how CI/CD logging practices can expose sensitive variables.
