---
id: scenario-01-cicd-leaks
title: CI/CD Leaks - Token Discovery & Lateral Movement
difficulty: intermediate
order: 2
flags:
  - name: Private Test Data Pipline
    pattern: "^flag\\{unused_[a-z0-9]{16}\\}$"
  - name: Private Test Data Unused Variable
    pattern: "^flag\\{lateral_movement_[a-z0-9]{16}\\}$"

solution:
  title: Solution
  content: |
    1. `pipeleek scan --artifacts --repo root/web-service`
    2. `PIPELEEK_GITLAB_TOKEN=glpat-[web-service-token] enum`
    3. `PIPELEEK_GITLAB_TOKEN=glpat-[web-service-token] variables`
    4. `PIPELEEK_GITLAB_TOKEN=glpat-[web-service-token] scan -a -r root/private-test-data`
hints:
  - title: Lateral Movement
    content: Pipeleek allows scanning artifacts using the `pipeleek scan --artifacts` flag.
  - title: Flags
    content: Using the additional PAT you can run a new scan and detect the flags in private repositories.
---

## Objective

Learn how to discover GitLab Personal Access Tokens (GLPAT) exposed in CI/CD pipelines, use them to access restricted resources, and extract secrets from project variables and build artifacts.

## Background

CI/CD pipelines often contain sensitive information that developers accidentally expose. If you are lucky you might find GitLab access tokens in the logs which will allow you to move laterally to e.g. private projects or dump more sensitive data due to higher acceess levels.

Sensitive values cannot only be found in pipeline logs, but also in generated Artifacts stored alongside the jobs ([Job Artifacts](https://docs.gitlab.com/ci/jobs/job_artifacts/), [Container Images](https://docs.gitlab.com/user/packages/container_registry/), [Releases](https://docs.gitlab.com/user/project/releases/) etc.).

## Scenario Description

### Phase 1: GitLab Access Token Discovery 

Using `pipeleek scan` try to find a personal access token that is being leaked on the GitLab instance.

> Tip: review the options of the scan command to increase your scan coverage.

### Phase 2: Lateral Movement

In possession of a new PAT you can again enumerate your newly discovered access with this new token.

> Tip: You can configure Pipeleek to use the new Token from an [environment variable](https://compasssecurity.github.io/pipeleek/introduction/configuration/#environment-variables) without having to change the config file. Example: `PIPELEEK_GITLAB_TOKEN=glpat-xxx pipeleek enum`

### Phase 3: Artifact Extraction (Environment Files)

Find all the flags

**Hint:** Sometimes not all configured variables are actually used.