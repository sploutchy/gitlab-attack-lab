# Recent Improvements

## Idempotent Project Creation

**Commit:** `38b8e33` - Add idempotent project creation (check if exists before creating)

### Problem
Re-running `make setup` would fail when trying to create projects that already exist, resulting in 400 Bad Request errors cascading through the rest of the setup process.

### Solution
Added project existence check in `create_project()` method:
- Before attempting to create a project, search for it by path
- If found, skip creation and reuse the existing project
- Still add/update variables, CI files, and schedules (in case these are new)

### Benefits
- ✅ Fully idempotent setup: `make setup` can be run multiple times without errors
- ✅ Graceful re-runs: Existing projects are reused, not recreated
- ✅ Cleaner output: "Project already exists" message instead of error
- ✅ Safe for iteration: Users can modify scenarios and re-run setup

### Code Pattern
```python
# Check if project already exists (idempotent re-runs)
search_path = project['path']
existing = self.api_call('GET', f'projects?search={search_path}')
if existing and len(existing) > 0:
    for p in existing:
        if p.get('path') == search_path:
            project_id = p['id']
            # Reuse existing project
            # Still add/update variables, CI, schedules
            return project_id

# Only create if not found
result = self.api_call('POST', 'projects', data)
```

### Related Improvements (Earlier Sessions)

1. **Group Idempotency** (already implemented)
   - Groups check if they exist before creation
   - Members fail with 409 but continue gracefully

2. **Runner Registration** (already implemented)
   - Runners check if they exist before creation
   - Only one runner per description

3. **Bash Variable Fixes** (already implemented)
   - Fixed newline parsing in REGISTERED variable
   - Prevents "integer expression expected" errors

4. **Enhanced Error Messaging** (already implemented)
   - Payload logging for failed project creation
   - Better 409 conflict messages for re-runs
   - Detailed API error responses

## Test Coverage
All 16 static tests pass:
- ✅ Python syntax validation
- ✅ YAML configuration validation
- ✅ Project structure checks
- ✅ Schedule validation
- ✅ Docker Compose validation

## What This Means for Users
- **Fresh Setup:** Works as before, creates all resources
- **Re-run Setup:** Can be safely executed without errors
- **Modify Config:** Change scenarios, re-run setup, updates apply
- **Clean Output:** Clear "already exists" messages instead of errors
