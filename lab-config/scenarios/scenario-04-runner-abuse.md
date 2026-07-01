---
id: scenario-04-runner-abuse
title: Shared Runner Host Breakout And Cross-Job Compromise
difficulty: advanced
order: 4
flags:
  - name: Runner Abuse Flag
    pattern: "^flag\\{runner_abuse_[a-z0-9]{16}\\}$"
solution:
  title: Solution
  content: |
    1. Identify which project gives you controlled execution on the shared runner.
    2. Validate a practical path from job context to runner host context.
    3. Enumerate other jobs that execute regularly on the same runner infrastructure.
    4. Collect runtime context from those recurring jobs and isolate the real flag.
hints:
  - title: Host Breakout First
    content: |
      Start from the project you can control and verify whether the shared runner
      context exposes host-level primitives.
  - title: Job Harvesting
    content: |
      After breakout, use runner-host visibility to enumerate and inspect recurring
      jobs from other projects.
      A purpose-built helper for this is [gl-runner-harvester](https://github.com/frjcomp/gl-runner-harvester).
  - title: Follow Scheduled Pipelines
    content: |
      The flag is not in your own attacker project output. Track scheduled pipelines
      and focus on cross-project runtime context.
---

## Objective

Exploit a shared runner misconfiguration to reach host context, then pivot into recurring jobs from other projects to recover the flag.

## Background

Shared runners can become a high-impact pivot point when isolation boundaries are weak. If an attacker escapes into runner host context, they may observe or interfere with unrelated jobs that run on the same infrastructure.

This scenario focuses on a multi-step chain:

1. Controlled CI execution on a shared runner
2. Breakout to runner host context
3. Cross-job collection from recurring pipelines
4. Flag extraction from collected runtime data

## Scenario Description

### Phase 1: Break Out Of The Shared Runner

Find the project where you can trigger reliable CI execution and use it as the initial foothold.

### Phase 2: Harvest Recurring Jobs

After breakout, enumerate jobs that execute on a schedule and collect their runtime context from runner host level.

If you are unfamiliar with runner-host collection tooling, use [gl-runner-harvester](https://github.com/frjcomp/gl-runner-harvester).
It is designed to watch active GitLab runner jobs and collect CI runtime data from host context.

Quick start example:

```bash
./gl-runner-harvester harvest --collection-path /tmp/gl-harvest --interval 2 --log-level info
```

### Phase 3: Extract The Flag

Differentiate noise from signal: recurring jobs may expose multiple secrets, but only one matches the scenario flag pattern.

> Important: the intended solve path requires both host breakout and cross-project recurring-job compromise.
