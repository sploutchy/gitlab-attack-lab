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
