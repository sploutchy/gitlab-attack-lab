---
id: scenario-01-cicd-leaks
title: CI/CD Leaks - Token Discovery & Exploitation
difficulty: intermediate
order: 3
flags:
  - name: GLPAT Token
    pattern: "^glpat-[A-Za-z0-9_-]{20}$"
  - name: Infrastructure Password
    pattern: "^flag\\{cicd_glpat_leak_[a-z0-9]{16}\\}$"
  - name: Artifact Environment
    pattern: "^flag\\{artifact_env_leak_[a-z0-9]{16}\\}$"
  - name: Dotenv Secret
    pattern: "^flag\\{dotenv_extracted_[a-z0-9]{16}\\}$"

solution:
  title: Solution
  content: |
    **Part 1: Token Discovery**
    1. Access the web-service project (root group) - it's public
    2. Navigate to CI/CD → Pipelines
    3. Click on the latest pipeline
    4. Click on the "setup" job to view logs
    5. Search for "glpat-" in the pipeline output
    6. Copy the full token: `glpat-xyz1234567890abc`
    7. This token has Owner (50) access to infrastructure-provisioner

    **Part 2: Token Exploitation**
    8. Start the pentester container: `make pentester-shell`
    9. Export the stolen token: `export GITLAB_TOKEN="glpat-xyz1234567890abc"`
    10. Use API or pipeleek to enumerate accessible projects
    11. Access infrastructure-provisioner project variables
    12. Extract FLAG_LEVEL1: `flag{cicd_glpat_leak_9f933f5d2a30}`

    **Part 3: Artifact Extraction - Environment File**
    13. Access infrastructure project (devops-team)
    14. Navigate to CI/CD → Pipelines
    15. Click on the "setup" job artifacts
    16. Download the .env file
    17. Extract FLAG_LEVEL2: `flag{artifact_env_leak_7d3e2c1a9b5f}`

    **Part 4: Artifact Extraction - Environment Dump**
    18. In the same pipelines, click on "build" job artifacts
    19. Download env_dump.txt
    20. Search for "flag{" patterns in the file
    21. Extract FLAG_LEVEL3: `flag{dotenv_extracted_b2e8f1c5a3d9}`
    22. Submit all flags for completion

hints:
  - title: Initial Discovery
    content: The web-service project is public and accessible without authentication. Start by exploring its CI/CD pipelines for exposed secrets or tokens.
  - title: Token Pattern
    content: GitLab Personal Access Tokens (GLPAT) follow the pattern `glpat-XXXXXXXXXXXXXXXX` where X is alphanumeric. Look for this in pipeline job logs.
  - title: Token Masking
    content: Some variables are intentionally NOT masked in this lab to simulate a security vulnerability. Check pipeline logs carefully for unmasked secrets.
  - title: Artifact Location
    content: CI/CD job artifacts are available in the "Job artifacts" section after pipelines complete. Look for downloadable files like .env and build outputs.
  - title: Using Stolen Tokens
    content: Once you have a token, you can use it to authenticate API requests or use tools like pipeleek. Export it as GITLAB_TOKEN environment variable.

---

# CI/CD Leaks - Token Discovery & Exploitation

## Objective
Learn how to discover GitLab Personal Access Tokens (GLPAT) exposed in CI/CD pipelines, use them to access restricted resources, and extract secrets from project variables and build artifacts.

## Background
CI/CD pipelines often contain sensitive information that developers accidentally expose:
- Unmasked variables in pipeline logs
- Secrets stored in build artifacts
- Access tokens with elevated privileges
- Credentials in environment files (.env, dotenv, etc.)

Developers sometimes misconfigure variables or leave debugging code in pipelines, leading to privilege escalation and data breaches.

## Scenario Steps

### Phase 1: Token Discovery (Public Access)
- Access the web-service project (it's public, no authentication needed)
- Review CI/CD pipelines to find exposed tokens
- Locate the GLPAT token in pipeline logs
- Note: Token has Owner-level access to other projects

### Phase 2: Token Exploitation (Privilege Escalation)
- Use the discovered token to authenticate to GitLab
- Access the restricted infrastructure-provisioner project
- Extract sensitive variables using the elevated access
- Retrieve secrets that were protected by Owner-level access

### Phase 3: Artifact Extraction (Environment Files)
- Access the infrastructure project
- Download .env files from pipeline artifacts
- Extract secrets directly from artifact files
- These secrets bypass normal access controls

### Phase 4: Complete Environment Dump
- Download environment dump artifacts
- Search for additional flags and secrets
- Understand how environment variables leak through artifacts

## Key Security Concepts

**Variable Masking:**
- ✅ Masked variables: Hidden in logs but still in environment
- ❌ Unmasked variables: Visible in plain text in pipeline logs

**Variable Protection:**
- ✅ Protected variables: Only run in protected branches/tags
- ❌ Unprotected variables: Available in all pipelines

**Artifact Security:**
- Artifacts are stored and may be accessible to users with project access
- Secrets in .env files within artifacts are permanently exposed
- Environment dumps capture all variables at pipeline execution time

**Access Levels:**
- 10 = Guest
- 20 = Reporter
- 30 = Developer ← Can see pipelines and artifacts
- 40 = Maintainer
- 50 = Owner ← Full project access including variables

## Security Lessons Learned

1. **Always mask sensitive variables** in CI/CD pipelines
2. **Protect variables** for restricted access
3. **Don't store secrets in artifacts** - use secret management systems
4. **Audit token usage** - monitor who can access what
5. **Use principle of least privilege** - tokens should have minimal required permissions
6. **Rotate tokens regularly** - especially if exposure is suspected
7. **Scan pipeline logs** - look for accidental secret exposure

## Challenge Difficulty: Intermediate
- Requires understanding of GitLab access levels
- Combines multiple exploitation techniques
- Tests knowledge of CI/CD security best practices
- Realistic attack scenario based on common misconfigurations
