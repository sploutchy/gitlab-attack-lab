# GitLab Attack Lab v1 Release Report

Date: 2026-07-01
Scope: Fresh rebuild, manual CTF-style validation of scenarios 00-04, issue triage for initial v1 release.

## Executive Summary

- Manual solves were completed for scenarios 00, 01, 02, 03, and 04.
- Disk exhaustion observed during validation is specific to this constrained development environment.
- Code-level setup and content issues identified during validation have now been fixed in-repo.

## Manual Validation Results

- Scenario 00: PASS
  - Retrieved welcome flag from security-tools scan job output.
  - Flag observed: flag{welcome_9f933f5d2a300d6b}

- Scenario 01: PASS (with caveat)
  - Initial pentester pipeleek configuration returned 401 Unauthorized.
  - After creating a fresh pentester PAT and configuring pipeleek, scan succeeded.
  - Flag observed: flag{cicd_vars_d78d62cc4824fa8f}

- Scenario 02: PASS
  - Found leaked PAT in web-service artifact (build_env.txt).
  - Used leaked PAT to access private-test-data and recover target token/flag.
  - Flag observed: flag{lateral_movement_589fd9ddb5b21182}

- Scenario 03: PASS (after runtime remediation)
  - Identified renovate-bot and generated autodiscovery exploit project.
  - Updated exploit payload to exfiltrate Renovate runtime environment via webhook logger.
  - Triggered private-app pipeline and recovered flag via webhook logs.
  - Flag observed: flag{renovate_a4f82b1c9e7d3056}

- Scenario 04: PASS (after runtime remediation)
  - Triggered attacker project pipeline and validated breakout jobs execute.
  - Verified recurring victim jobs and recovered target flag from payroll-batch trace.
  - Flag observed: flag{runner_abuse_5f3d91b2a4c7e8d1}

## Findings (Ordered by Severity)

### 1) ENVIRONMENT NOTE - Platform disk exhaustion causes global GitLab API failure

- Symptom:
  - GitLab API endpoints started returning HTTP 500 globally.
  - Scenario validation halted mid-run.

- Evidence:
  - GitLab logs showed repeated:
    - No space left on device
    - Redis MISCONF (RDB snapshot write failures)
  - Affected endpoints included:
    - /api/v4/user
    - /api/v4/projects
    - /api/v4/runners/all

- Reproduction:
  1. Run full setup and scenario activity until filesystem pressure increases.
  2. Observe overlay/workspaces filesystem reaching 100%.
  3. GitLab transitions into 500 responses due to Redis write protection behavior.

- Impact in this environment:
  - Entire lab becomes unusable (all scenarios blocked).
  - False negatives in deployment/manual tests.

- Temporary remediation used in this validation:
  - docker builder prune -af
  - docker image prune -af
  - This restored free space and API health.

- Note:
  - This is not treated as an intrinsic lab-content defect and is environment-specific.

### 2) HIGH - Runner tag mismatch makes scenarios 03/04 unschedulable on fresh rebuild

- Symptom:
  - Jobs remained pending indefinitely:
    - private-app renovate job (scenario 03)
    - runner-breakout-lab jobs and recurring victim jobs (scenario 04)

- Root cause:
  - CI templates require tags:
    - scenario 03: docker
    - scenario 04: docker, shared
  - Registered instance runner appeared untagged in initial state, so tagged jobs had no eligible executor.

- Reproduction:
  1. Fresh rebuild.
  2. Trigger pipeline for private-app or runner-breakout-lab.
  3. Observe jobs stay pending with no matching runner.

- Impact:
  - Scenarios 03 and 04 are unsolvable for players.

- Temporary remediation used in this validation:
  - Updated runner 1 tags at runtime to docker,shared.
  - Immediately after, scenarios 03/04 pipelines executed successfully.

- Recommended fix:
  - Enforce deterministic runner registration/tagging during setup/population.
  - Add deployment test assertion verifying at least one online runner matches required tags.

- Status:
  - Fixed in setup flow and deployment tests.

### 3) MEDIUM - Preconfigured pentester pipeleek token invalid after rebuild

- Symptom:
  - pipeleek scan in pentester container returned 401 Unauthorized.

- Reproduction:
  1. Fresh rebuild.
  2. Execute pipeleek scan from pentester container with default config.
  3. Observe API 401 responses.

- Impact:
  - Scenario 01 onboarding appears broken for new players until they manually create/configure PAT.

- Workaround used in validation:
  - Create fresh pentester PAT via admin API and write token into pentester pipeleek config.

- Recommended fix:
  - Ensure pentester tooling config is either:
    - generated dynamically from current seeded token, or
    - intentionally blank with explicit in-lab step to create PAT.

- Status:
  - Fixed in setup flow by minting a fresh pentester PAT and writing runtime tool config from it.

### 4) MEDIUM - Scenario 03 guidance uses CLI command aliases that do not match installed binary behavior

- Symptom:
  - Documented commands pipeleek gl ... and pipeleek gh ... failed as unknown commands in current pentester image.

- Reproduction:
  1. Run documented scenario 03 solution command strings exactly.
  2. Observe unknown command errors.

- Impact:
  - Player confusion/friction and increased support burden.

- Recommended fix:
  - Align scenario markdown command examples with installed CLI entrypoint behavior (e.g., pipeleek renovate bots and pipeleek renovate autodiscovery ...).
  - Add one verified command block copied from current tool version.

- Status:
  - Fixed in scenario markdown command examples.

## Release Readiness Assessment

- Current recommendation: code-level findings are addressed; re-run full fresh rebuild plus manual scenario sweep to confirm no regressions.
- Environment note: ensure sufficient host/workspace disk capacity in this dev environment before long validation runs.

## Notes About Validation Environment

- Runtime-only corrective actions were applied during this pass to complete end-to-end validation:
  - Docker storage cleanup to recover disk space.
  - Runner tag adjustment for matching tagged jobs.
- These were operational test actions, not committed source changes.