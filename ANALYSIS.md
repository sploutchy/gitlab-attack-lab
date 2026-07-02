# Job Queueing Analysis - root/qa-automation job #29

## Current Situation

**Job Status:**
- Job ID: 29 (qa-automation/test)
- Status: Pending/Waiting
- Queued Duration: 304+ seconds (5+ minutes!)
- Requires tag: "docker"
- Runner assigned: None (still waiting for capacity)

**Runner Configuration:**
```
Runner 1: shared-docker-runner (ONLINE, ACTIVE)
  - Tags: ["docker", "linux", "shared"]
  - Executor: Docker
  - Status: online, job_execution_status: active
  - Limit per runner: 5
  
Runner 2: shell-runner (ONLINE, IDLE)
  - Tags: ["shell", "privileged"]
  - Executor: Shell
  - Status: online, job_execution_status: idle
  - Limit per runner: 5
```

## Root Cause: Global Concurrency Bottleneck ❌

**The Problem:**
Both runners have `concurrent = 1` in their config.toml:
```toml
concurrent = 1              # ← BOTTLENECK: Only 1 job can run at a time globally!
check_interval = 0
```

Even though:
- Each runner has `limit = 5` (can handle 5 jobs each)
- Runners are online and healthy
- Docker runner is currently executing 1 job

The global `concurrent = 1` setting means the GitLab Runner Manager can only start **ONE job total** across **ALL runners**, regardless of runner configuration.

## Impact

When one job is running on the docker runner:
```
Global concurrency limit reached (1/1)
  ↓
Job 29 cannot start even though runner has capacity
  ↓
Job waits indefinitely in queue
  ↓
Setup appears slow or broken
```

## Solution: Increase Global Concurrency

**Recommended Change:**
```toml
concurrent = 4              # Allow up to 4 jobs to run in parallel
```

This allows:
- Up to 4 jobs to run simultaneously across all runners
- Multiple jobs on docker runner (up to 5 per runner limit)
- Scenarios 02-04 to execute jobs in parallel
- Much faster test execution and scenario setup

## Where to Apply Fix

**File:** docker-compose.yml

Both runner services register without setting concurrent value, so it defaults to 1.

**Fix Implementation:**
Update the docker-compose.yml to pass `--concurrent` flag when registering runners, OR modify the runner config after registration via a setup script.

### Approach 1: Config File Method (Recommended)
Pre-create config.toml with correct concurrent value and mount it into runner containers.

### Approach 2: Post-Registration Modification
Add script to setup.sh that updates config.toml after runner registration.

### Approach 3: Increase Limits Even More
Use `concurrent = 8` to allow truly parallel execution across all runners (docker runner limit 5 + shell runner limit 5 = 10 potential slots, use 8 to be safe).
