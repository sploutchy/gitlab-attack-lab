# Setup Troubleshooting & Expected Output

## What to Expect When Running `make setup`

### Timeline

1. **Services Start** (~5-10 seconds)
   - ✓ Docker Compose starts gitlab, runners, mailhog, pentester, shell-runner

2. **GitLab Initialization** (~30-60 seconds)
   - First time: Full initialization needed
   - Subsequent runs: Much faster
   - Watch: `docker-compose logs gitlab` if concerned

3. **Configuration & Population** (~30-60 seconds)
   - Creates users, groups, projects
   - Imports repositories from GitHub
   - Creates variables and CI files
   - **File creation now retries automatically** (3 attempts, 3-second delays)
   - **Schedules now skip if CI file missing** (will retry)

4. **Runner Registration** (~30-60 seconds)  
   - **Wait timeout increased to 60 seconds** (was 30)
   - Runners register and come online
   - Expected: "✓ Runners registered and online (2 runners)"

5. **Pentester Container** (~10-20 seconds)
   - **Now starts independently** (no strict dependencies)
   - Waits up to 30 seconds for readiness
   - Creates pipeleek configuration
   - Sets environment variables

6. **Final Summary**
   - ✓ Clean run: "Setup Complete! 🎉"
   - ⚠ With warnings: "Setup Complete with Warnings ⚠"

### Expected Messages (Normal Operation)

```
[STEP 1] Starting Docker Compose services...
✓ Services started

[STEP 2] Waiting for GitLab to initialize...
✓ GitLab is ready (took Xs)

[STEP 3] Setting root password and creating admin token...
✓ Admin token created: glpat-...

[STEP 4] Populating GitLab structure from configuration...
Merged configuration written to /tmp/gitlab-lab-merged.yml
[OK] GitLab is ready!
[OK] Created user: pentester (ID: 2)
[OK] Created group: security-team (ID: 6)
[OK] Created project: web-app (ID: 1)
[INFO] Cloning https://github.com/octocat/Hello-World.git...
[OK] Repository imported successfully for project 1
[OK] Added variable DEPLOY_ENV to project 1
[INFO] File creation failed for project 1, retrying in 3 seconds... (attempt 1/3)
[OK] Created .gitlab-ci.yml in project 1
[OK] Added schedule to project 1
[INFO] Creating runners...
[OK] Created runner: shared-docker-runner
[OK] Population complete!

✓ GitLab populated successfully!

Waiting for runners to register and come online...
✓ Runners registered and online (2 runners)

[STEP 5] Configuring pentester container...
✓ Pentester container configured with pipeleek

✅ Setup Complete! 🎉
✓ All services running
✓ GitLab populated with lab data
✓ Pentester container ready

Enter pentester container now? (y/n)
```

## Expected Error Handling

### File Creation Retries (NEW)

```
[ERROR] API call failed: 400 Client Error: Bad Request for .gitlab-ci.yml
[INFO] File creation failed for project 1, retrying in 3 seconds... (attempt 1/3)
[OK] Created .gitlab-ci.yml in project 1  ← Retried successfully!
```

This is **normal and expected** - the fix automatically handles it!

### Runner Wait (Extended Timeout)

```
Waiting for runners to register and come online...
[1/30] Checking... (1 runners online)
[2/30] Checking... (1 runners online)
... (waits up to 60 seconds now, was 30)
✓ Runners registered and online (2 runners)
```

### Pentester Container (Improved)

```
[STEP 5] Configuring pentester container...
✓ Pentester container configured with pipeleek

# If container takes time:
Configuring pentester container...
(waiting up to 30 seconds for container to be ready)
✓ Pentester container configured with pipeleek
```

## Troubleshooting

### Issue: "Only 00 runners online"

**Likely Causes:**
1. Runners still starting (wait longer)
2. Docker issues
3. Runner container failed

**Solutions:**
```bash
# Check runner status
docker-compose ps

# View runner logs
docker-compose logs shared-docker-runner
docker-compose logs shell-runner

# Restart runners
docker-compose restart shared-docker-runner shell-runner

# Rebuild runners from scratch
docker-compose down shared-docker-runner shell-runner
make setup
```

### Issue: "Pentester container is not running"

**Likely Causes:**
1. Container build failed
2. Insufficient resources
3. Network issues

**Solutions:**
```bash
# Check pentester logs
docker-compose logs pentester

# Rebuild pentester
docker-compose build pentester
docker-compose up -d pentester

# Check if container is running
docker-compose ps pentester

# Enter manually later
docker-compose exec -it pentester /bin/bash
```

### Issue: ".gitlab-ci.yml still not created after retries"

**Likely Causes:**
1. GitLab API issue
2. Invalid CI file syntax in scenario
3. Project corrupted

**Solutions:**
```bash
# Check GitLab logs
docker-compose logs gitlab | tail -100

# Check the specific project
curl -s http://127.0.0.1/api/v4/projects/1 -H "PRIVATE-TOKEN: glpat-..." | jq

# Manually create CI file via GitLab UI
# 1. Go to http://127.0.0.1
# 2. Navigate to project
# 3. Create .gitlab-ci.yml file directly
```

### Issue: "Setup Complete with Warnings ⚠"

This is **normal on re-runs** - expected warnings:
- Group members already exist (409 conflicts) → OK, already in group
- Some file creation fails then succeeds on retry → OK, eventual success

Real errors to watch:
- Multiple "ERROR" lines in output
- "Population complete!" not shown
- Projects showing status != "OK"

## Re-running Setup

✅ **Safe to re-run** - System is now fully idempotent!

```bash
# On fresh Docker containers
make setup

# To update configuration after modifying scenarios
make setup

# To create runner tokens again
docker-compose down
docker-compose up -d
make setup
```

Each component checks if it exists before creating:
- **Users**: Skips if exists
- **Groups**: Reuses if exists, adds new members
- **Projects**: Reuses if exists, updates variables/CI/schedules
- **Runners**: Checks before registering
- **Schedules**: Skips if already exists

## Success Criteria

✅ Setup is successful when:
- GitLab is running and accessible
- All users created (root, pentester, alice, bob, charlie)
- All groups created with members assigned
- All projects created with repositories imported
- CI files created (after retries if needed)
- Schedules created and active
- Runners online and registered (2 total)
- Pentester container running with pipeleek configured
- Can access http://127.0.0.1 and log in

## Performance Tips

1. **First run takes longer** (10-15 minutes)
   - GitLab needs full initialization
   - GitHub repos need to be cloned
   - Docker images built/pulled

2. **Subsequent runs are faster** (2-5 minutes)
   - Containers already running
   - Configurations reused
   - File retries usually succeed on first attempt

3. **To speed up re-runs**:
   ```bash
   # Don't remove persistent data
   make setup  # Instead of docker-compose down first
   ```

## Next Steps After Setup

1. **Verify Everything Works**
   ```bash
   docker-compose ps              # All services running?
   curl http://127.0.0.1          # GitLab responds?
   make test-static               # All tests pass?
   ```

2. **Access GitLab**
   - URL: http://127.0.0.1
   - Username: root
   - Password: R00t@L4b_Adm1n_2024

3. **Enter Pentester Container**
   ```bash
   docker-compose exec -it pentester /bin/bash
   pipeleek gl enum                # Try pipeleek commands
   ```

4. **Explore Lab Structure**
   - Projects: web-app, api-service, mobile-app, infrastructure, security-tools, web-service, infrastructure-provisioner, qa-automation
   - Users: root (admin), pentester, alice, bob, charlie
   - Groups: security-team, devops-team, development-team
   - Scenarios: default, scenario-1 (Public CI/CD)
