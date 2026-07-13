#!/bin/bash
# setup.sh - Complete one-command setup that starts everything

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Load environment
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo "[-] .env file not found!"
    exit 1
fi

GITLAB_HOST_URL="${GITLAB_HOST_URL:-http://127.0.0.1:7700}"
GITLAB_HOST_URL="${GITLAB_HOST_URL%/}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║         GitLab Attack Lab - Complete Setup                     ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 0: Pre-pull CI job images so pipelines do not repeatedly hit Docker Hub
echo -e "${YELLOW}[STEP 0]${NC} Pre-pulling CI runner images (best effort)..."
CI_PREPULL_IMAGES=${CI_PREPULL_IMAGES:-"alpine:latest alpine:3.19 alpine:3.20 ubuntu:latest ubuntu:24.04 node:18 python:3.11 renovate/renovate:37-full"}
PREPULL_FAILED=0

for IMAGE in $CI_PREPULL_IMAGES; do
    echo -e "  Pulling $IMAGE"
    PULL_OK=0

    for ATTEMPT in 1 2 3; do
        if docker pull "$IMAGE" >/tmp/gitlab-setup-image-pull.log 2>&1; then
            echo -e "${GREEN}  ✓${NC} Pulled $IMAGE"
            PULL_OK=1
            break
        fi

        if [ "$ATTEMPT" -lt 3 ]; then
            echo -e "${YELLOW}  •${NC} Retry $ATTEMPT failed for $IMAGE, retrying..."
            sleep 2
        fi
    done

    if [ "$PULL_OK" -ne 1 ]; then
        PREPULL_FAILED=$((PREPULL_FAILED + 1))
        echo -e "${YELLOW}  ⚠${NC} Could not pre-pull $IMAGE (continuing setup)"
        tail -n 5 /tmp/gitlab-setup-image-pull.log || true
    fi
done

if [ "$PREPULL_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} CI runner images pre-pulled"
else
    echo -e "${YELLOW}⚠${NC} ${PREPULL_FAILED} image(s) could not be pre-pulled; setup will continue"
fi
echo ""

# Step 1: Start Docker Compose services
echo -e "${YELLOW}[STEP 1]${NC} Starting Docker Compose services..."
cd "$PROJECT_ROOT"
if ! docker-compose up -d >/tmp/gitlab-setup-compose-up.log 2>&1; then
    echo -e "${RED}✗${NC} Failed to start Docker Compose services"
    tail -n 50 /tmp/gitlab-setup-compose-up.log || true
    exit 1
fi
echo -e "${GREEN}✓${NC} Services started"
echo ""

# Step 2: Wait for GitLab to be healthy
echo -e "${YELLOW}[STEP 2]${NC} Waiting for GitLab to initialize (this may take 5-10 minutes)..."
ATTEMPT=0
MAX_WAIT_SECONDS=1200
while true; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Try to access GitLab API - don't require container to be healthy, just accessible
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$GITLAB_HOST_URL/api/v4/version" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
        echo -e "${GREEN}✓${NC} GitLab is ready (took ${ATTEMPT}s)"
        break
    fi
    
    # Show progress every 30 seconds
    if [ $((ATTEMPT % 30)) -eq 0 ]; then
        STATUS=$(docker ps --filter "name=^/gitlab-attack-lab$" --format "{{.Status}}" | head -n 1)
        if [ -z "$STATUS" ]; then
            STATUS="not running"
        fi
        echo -e "  Waiting... (${ATTEMPT}s elapsed) - Container: $STATUS"

        GITLAB_STATE_ERROR=$(docker inspect gitlab-attack-lab --format '{{.State.Error}}' 2>/dev/null || true)
        if [ -n "$GITLAB_STATE_ERROR" ]; then
            echo -e "${RED}✗${NC} GitLab container failed to start"
            echo -e "${YELLOW}Docker error:${NC} $GITLAB_STATE_ERROR"
            exit 1
        fi
    fi

    if [ "$ATTEMPT" -ge "$MAX_WAIT_SECONDS" ]; then
        echo -e "${RED}✗${NC} GitLab did not become reachable within ${MAX_WAIT_SECONDS}s"
        echo -e "${YELLOW}Recent GitLab logs:${NC}"
        docker-compose logs --tail=80 gitlab || true
        exit 1
    fi
    sleep 1
done
echo ""

# Step 3: Set root password and create admin token
echo -e "${YELLOW}[STEP 3]${NC} Setting root password and creating admin token..."

# First, set the root password and ensure admin status
echo -e "  Setting password..."
docker exec gitlab-attack-lab gitlab-rails runner \
    'u=User.find_by(username:"root");u.update(password:"R00t@L4b_Adm1n_2024",password_confirmation:"R00t@L4b_Adm1n_2024",admin:true);u.update(locked: false, state: :active);puts "Password set"' 2>&1 | grep -q "Password set" && echo -e "${GREEN}  ✓${NC} Password set" || echo -e "${YELLOW}  Note: Password may already be set${NC}"

# Wait a moment for the user to be ready
sleep 2

# Create the admin token with all scopes
echo -e "  Creating admin token..."
TOKEN_OUTPUT=$(docker exec gitlab-attack-lab gitlab-rails runner \
    "user = User.find_by(username: 'root'); token_name = 'lab-admin-token-' + Time.now.to_i.to_s; token = user.personal_access_tokens.create!(scopes: [:api, :read_user, :read_api, :read_repository, :write_repository, :admin_mode, :sudo], name: token_name, expires_at: 1.year.from_now); puts token.token" 2>&1)

# Extract the token (last line of output)
NEW_TOKEN=$(echo "$TOKEN_OUTPUT" | grep "glpat-" | tail -1)

if [ -n "$NEW_TOKEN" ]; then
    echo -e "${GREEN}  ✓${NC} Admin token created: ${NEW_TOKEN:0:20}..."
    
    # Update .env file with the new token
    if [ -f "$PROJECT_ROOT/.env" ]; then
        sed -i "s/^GITLAB_ADMIN_TOKEN=.*/GITLAB_ADMIN_TOKEN=$NEW_TOKEN/" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}  ✓${NC} Updated .env with new token"
    fi
    
    # Update the environment variable for this script
    GITLAB_ADMIN_TOKEN="$NEW_TOKEN"

    # Ensure the token is usable before population (GitLab can briefly return 502 after startup)
    echo -e "  Verifying admin token with GitLab API..."
    TOKEN_READY=0
    for i in $(seq 1 30); do
        USER_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" "$GITLAB_HOST_URL/api/v4/user" 2>/dev/null || echo "000")
        if [ "$USER_HTTP_CODE" = "200" ]; then
            TOKEN_READY=1
            echo -e "${GREEN}  ✓${NC} Admin token verified"
            break
        fi
        sleep 2
    done

    if [ "$TOKEN_READY" -ne 1 ]; then
        echo -e "${YELLOW}  ⚠${NC}  Admin token not yet accepted by API, population step will retry auth"
    fi
else
    echo -e "${YELLOW}  ⚠${NC}  Could not create new token, using existing token from .env"
fi

echo ""

# Step 3.5: Disable Auto DevOps globally
echo -e "${YELLOW}[STEP 3.5]${NC} Disabling GitLab Auto DevOps globally..."
AUTO_DEVOPS_DISABLED=0
for i in $(seq 1 20); do
    HTTP_CODE=$(curl -s -o /tmp/gitlab-settings-response.json -w "%{http_code}" \
        -X PUT \
        -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
        --data-urlencode "auto_devops_enabled=false" \
        "$GITLAB_HOST_URL/api/v4/application/settings" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        if grep -q '"auto_devops_enabled":false' /tmp/gitlab-settings-response.json; then
            AUTO_DEVOPS_DISABLED=1
            echo -e "${GREEN}  ✓${NC} Auto DevOps disabled globally"
            break
        fi
    fi

    sleep 2
done

if [ "$AUTO_DEVOPS_DISABLED" -ne 1 ]; then
    echo -e "${YELLOW}  ⚠${NC}  Could not confirm Auto DevOps global disablement"
fi

echo ""

# Step 4: Populate GitLab structure from YAML
echo -e "${YELLOW}[STEP 4]${NC} Populating GitLab structure from configuration..."
cd "$PROJECT_ROOT"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗${NC} Python3 not found. Installing..."
    apt-get update > /dev/null 2>&1
    apt-get install -y python3 python3-pip > /dev/null 2>&1
fi

# Install required Python packages
pip3 install -q pyyaml requests 2>/dev/null || true

# Merge scenarios into a single config
MERGED_CONFIG="/tmp/gitlab-lab-merged.yml"
SCENARIO_INPUTS=${SCENARIOS:-"$PROJECT_ROOT/lab-config/scenarios"}

echo -e "${YELLOW}  •${NC} Installing Python dependencies..."
pip3 install -q -r "$PROJECT_ROOT/scripts/requirements.txt" 2>&1 | grep -v "already satisfied" || true

echo -e "${YELLOW}  •${NC} Merging scenario files..."
python3 "$PROJECT_ROOT/scripts/merge-scenarios.py" \
    --base "$PROJECT_ROOT/lab-config/base.yml" \
    --scenarios $SCENARIO_INPUTS \
    --output "$MERGED_CONFIG" 2>&1

# Run the populator and capture runner tokens
set +e
POPULATE_OUTPUT=$(python3 "$PROJECT_ROOT/scripts/populate-gitlab.py" "$MERGED_CONFIG" "$GITLAB_HOST_URL" "$GITLAB_ADMIN_TOKEN" 2>&1)
POPULATE_EXIT=$?
set -e

echo "$POPULATE_OUTPUT" | grep -v "^===" | grep -v "=" || true

# Check for errors and warnings in the output
ERROR_COUNT=$(echo "$POPULATE_OUTPUT" | grep -c "^\[   ERROR\]" || true)
WARN_COUNT=$(echo "$POPULATE_OUTPUT" | grep -c "^\[    WARN\]" || true)

if [ $POPULATE_EXIT -eq 0 ]; then
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC} GitLab structure populated with ${ERROR_COUNT} errors and ${WARN_COUNT} warnings"
    elif [ $WARN_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC} GitLab structure populated with ${WARN_COUNT} warnings"
    else
        echo -e "${GREEN}✓${NC} GitLab structure populated successfully"
    fi
    
    # Extract and save runner tokens to .env
    if echo "$POPULATE_OUTPUT" | grep -q "=== RUNNER_TOKENS ==="; then
        # First, reload .env to get updated variables
        source "$PROJECT_ROOT/.env"
        
        echo "$POPULATE_OUTPUT" | sed -n '/=== RUNNER_TOKENS ===/,/=== END_RUNNER_TOKENS ===/p' | grep '=' | grep -v "===" | while IFS='=' read -r runner_name token; do
            # Convert description to env var format (e.g., shared-docker-runner -> RUNNER_TOKEN_DOCKER)
            if [[ "$runner_name" == *"docker"* ]]; then
                sed -i "s/^RUNNER_TOKEN_DOCKER=.*/RUNNER_TOKEN_DOCKER=$token/" "$PROJECT_ROOT/.env"
                echo -e "${GREEN}  ✓${NC} Saved docker runner token"
            elif [[ "$runner_name" == *"shell"* ]]; then
                sed -i "s/^RUNNER_TOKEN_SHELL=.*/RUNNER_TOKEN_SHELL=$token/" "$PROJECT_ROOT/.env"
                echo -e "${GREEN}  ✓${NC} Saved shell runner token"
            fi
        done
        
        # Reload environment after updating .env
        source "$PROJECT_ROOT/.env"
        
        # Remove old runner containers to force recreation with new env vars
        echo -e "  Removing old runner containers..."
        docker-compose rm -f gitlab-runner-docker gitlab-runner-shell > /dev/null 2>&1 || true
        
        # Recreate runner containers with new tokens from .env
        echo -e "  Creating runner containers with new tokens..."
        if ! docker-compose up -d gitlab-runner-docker gitlab-runner-shell 2>&1 | tee /tmp/runner-create.log | grep -v "^$" > /dev/null; then
            echo -e "${YELLOW}  ⚠${NC}  Warning during runner container creation (see /tmp/runner-create.log)"
        fi
        
        # Wait for runners to be registered via GitLab API (before setting tags)
        echo -e "  Waiting for runners to register with GitLab..."
        RUNNER_REG_WAIT=0
        while [ $RUNNER_REG_WAIT -lt 30 ]; do
            RUNNER_COUNT=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
                "$GITLAB_HOST_URL/api/v4/runners/all?per_page=100" 2>/dev/null | jq 'length' || echo 0)
            
            if [ "$RUNNER_COUNT" -ge 2 ]; then
                echo -e "${GREEN}  ✓${NC} Runners registered with GitLab (found $RUNNER_COUNT)"
                break
            fi
            
            sleep 2
            RUNNER_REG_WAIT=$((RUNNER_REG_WAIT + 2))
        done
        
        # Set runner tags via API (required in GitLab 19.1+)
        echo -e "  Setting runner tags via API..."
        GITLAB_HOST_URL="$GITLAB_HOST_URL" GITLAB_ADMIN_TOKEN="$GITLAB_ADMIN_TOKEN" python3 - <<'PYTHON_SET_TAGS'
import os
import requests
import json

url = os.environ.get("GITLAB_HOST_URL", "").rstrip("/")
token = os.environ.get("GITLAB_ADMIN_TOKEN", "")

session = requests.Session()
session.headers.update({"PRIVATE-TOKEN": token})

try:
    # Get all runners
    runners_resp = session.get(f"{url}/api/v4/runners/all", params={"per_page": 100}, timeout=10)
    runners = runners_resp.json()
    
    # Map descriptions to expected tags
    tag_mapping = {
        "shared-docker-runner": ["docker", "linux", "shared"],
        "shell-runner": ["shell", "privileged"],
    }
    
    for runner in runners:
        desc = runner.get("description", "")
        runner_id = runner.get("id")
        
        if desc in tag_mapping:
            expected_tags = tag_mapping[desc]
            current_tags = runner.get("tag_list") or []
            
            # Only update if tags are missing
            if set(current_tags) != set(expected_tags):
                update_resp = session.put(
                    f"{url}/api/v4/runners/{runner_id}",
                    json={"tag_list": expected_tags},
                    timeout=10
                )
                
                if update_resp.status_code == 200:
                    print(f"✓ Updated {desc} tags to {expected_tags}")
                else:
                    print(f"⚠ Failed to update {desc} tags: {update_resp.status_code}")
            else:
                print(f"✓ {desc} already has correct tags: {expected_tags}")
except Exception as e:
    print(f"Error setting runner tags: {e}")
PYTHON_SET_TAGS
        
        # Wait for runners to register with expected tags (up to 60 seconds)
        echo -e "  Waiting for runners to register with expected tags..."
        RUNNER_WAIT=0
        RUNNERS_FOUND=0
        while [ $RUNNER_WAIT -lt 60 ]; do
            RUNNER_CHECK=$(GITLAB_HOST_URL="$GITLAB_HOST_URL" GITLAB_ADMIN_TOKEN="$GITLAB_ADMIN_TOKEN" python3 - <<'PY'
import os
import requests

url = os.environ.get("GITLAB_HOST_URL", "").rstrip("/")
token = os.environ.get("GITLAB_ADMIN_TOKEN", "")

expected = {
    "shared-docker-runner": {"docker", "linux", "shared"},
    "shell-runner": {"shell"},
}

try:
    session = requests.Session()
    session.headers.update({"PRIVATE-TOKEN": token})

    runners_resp = session.get(f"{url}/api/v4/runners/all", params={"per_page": 100}, timeout=10)
    if runners_resp.status_code != 200:
        print(f"api_status={runners_resp.status_code}")
        raise SystemExit(0)

    runners = runners_resp.json()
    by_description = {}
    for runner in runners:
        description = runner.get("description")
        by_description.setdefault(description, []).append(runner)

    missing = []
    missing_tags = []
    for description, tags in expected.items():
        candidates = by_description.get(description, [])
        if not candidates:
            missing.append(description)
            continue

        has_eligible_runner = False
        for candidate in candidates:
            details_resp = session.get(f"{url}/api/v4/runners/{candidate['id']}", timeout=10)
            if details_resp.status_code != 200:
                continue

            details = details_resp.json()
            if details.get("status") != "online":
                continue

            actual_tags = set(details.get("tag_list") or [])
            if tags.issubset(actual_tags):
                has_eligible_runner = True
                break

        if not has_eligible_runner:
            missing_tags.append(description)

    if missing or missing_tags:
        print(f"not_ready missing={','.join(missing)} missing_tags={','.join(missing_tags)}")
    else:
        online_count = sum(1 for runner in runners if runner.get("status") == "online")
        print(f"ready online={online_count}")
except Exception as err:
    print(f"check_error={err}")
PY
)

            if [[ "$RUNNER_CHECK" == ready* ]]; then
                REGISTERED=$(echo "$RUNNER_CHECK" | sed -n 's/.*online=\([0-9]\+\).*/\1/p')
                [ -z "$REGISTERED" ] && REGISTERED="2"
                echo -e "${GREEN}  ✓${NC} Runners are online and tag-matched (${REGISTERED} online)"
                RUNNERS_FOUND=1
                break
            fi
            
            sleep 2
            RUNNER_WAIT=$((RUNNER_WAIT + 2))
        done
        
        if [ "$RUNNERS_FOUND" -ne 1 ]; then
            echo -e "${YELLOW}  ⚠${NC}  Runner readiness check did not pass: ${RUNNER_CHECK}"
            echo -e "${YELLOW}     Tagged jobs may stay pending until runner registration completes${NC}"
        fi
    fi
else
    echo -e "${RED}✗${NC} Failed to populate GitLab structure"
    exit 1
fi
echo ""

# Step 5: Validate runners and scenario readiness
echo -e "${YELLOW}[STEP 5]${NC} Validating runners and scenario readiness..."
echo -e "${YELLOW}         (This may take several minutes as jobs execute)${NC}"
echo ""

if ! GITLAB_HOST_URL="$GITLAB_HOST_URL" GITLAB_ADMIN_TOKEN="$GITLAB_ADMIN_TOKEN" VALIDATION_TIMEOUT=600 python3 "$PROJECT_ROOT/scripts/validate-runners.py"; then
    echo ""
    echo -e "${YELLOW}⚠${NC}  Validation incomplete or timed out"
    echo -e "${YELLOW}     Some scenarios may not be ready yet. You can:"
    echo -e "${YELLOW}     1. Wait a few minutes and try again (jobs may still be running)"
    echo -e "${YELLOW}     2. Check job status at: http://$GITLAB_HOST_URL/dashboard/projects"
    echo -e "${YELLOW}     3. Run: GITLAB_HOST_URL=$GITLAB_HOST_URL GITLAB_ADMIN_TOKEN=$GITLAB_ADMIN_TOKEN python3 $PROJECT_ROOT/scripts/validate-runners.py${NC}"
fi
echo ""

# Step 6: Configure pentester container
echo -e "${YELLOW}[STEP 6]${NC} Configuring pentester container..."

# Wait for pentester container to be running (up to 30 seconds)
PENTESTER_WAIT=0
while [ $PENTESTER_WAIT -lt 30 ]; do
    if docker exec pentester true 2>/dev/null; then
        break
    fi
    sleep 1
    PENTESTER_WAIT=$((PENTESTER_WAIT + 1))
done

if ! docker exec pentester true 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} Pentester container not responding, skipping configuration"
    echo -e "${YELLOW}   You may need to manually run: docker-compose logs pentester${NC}"
else
    # Create a dedicated pentester token for player workflows
    echo -e "  Creating pentester API token..."
    NEW_PENTESTER_TOKEN=$(GITLAB_HOST_URL="$GITLAB_HOST_URL" GITLAB_ADMIN_TOKEN="$GITLAB_ADMIN_TOKEN" python3 - <<'PY'
import os
import time
from datetime import datetime, timedelta, timezone

import requests

url = os.environ.get("GITLAB_HOST_URL", "").rstrip("/")
admin_token = os.environ.get("GITLAB_ADMIN_TOKEN", "")

session = requests.Session()
session.headers.update({"PRIVATE-TOKEN": admin_token})

try:
    users_resp = session.get(f"{url}/api/v4/users", params={"username": "pentester", "per_page": 100}, timeout=15)
    users_resp.raise_for_status()
    users = users_resp.json()
    pentester = next((u for u in users if u.get("username") == "pentester"), None)
    if not pentester:
        print("")
        raise SystemExit(0)

    expires_at = (datetime.now(timezone.utc) + timedelta(days=365)).date().isoformat()
    token_name = f"pentester-lab-token-{int(time.time())}"
    token_resp = session.post(
        f"{url}/api/v4/users/{pentester['id']}/personal_access_tokens",
        data=[
            ("name", token_name),
            ("expires_at", expires_at),
            ("scopes[]", "api"),
            ("scopes[]", "read_api"),
            ("scopes[]", "read_repository"),
        ],
        timeout=15,
    )
    if token_resp.status_code not in (200, 201):
        print("")
        raise SystemExit(0)

    print(token_resp.json().get("token", ""))
except Exception:
    print("")
PY
)

    ACTIVE_PENTESTER_TOKEN=""
    if [ -n "$NEW_PENTESTER_TOKEN" ]; then
        ACTIVE_PENTESTER_TOKEN="$NEW_PENTESTER_TOKEN"
        if grep -q '^PENTESTER_TOKEN=' "$PROJECT_ROOT/.env"; then
            sed -i "s/^PENTESTER_TOKEN=.*/PENTESTER_TOKEN=$ACTIVE_PENTESTER_TOKEN/" "$PROJECT_ROOT/.env"
        else
            echo "PENTESTER_TOKEN=$ACTIVE_PENTESTER_TOKEN" >> "$PROJECT_ROOT/.env"
        fi
        echo -e "${GREEN}  ✓${NC} Created pentester token and saved to .env"
    elif [ -n "$PENTESTER_TOKEN" ]; then
        ACTIVE_PENTESTER_TOKEN="$PENTESTER_TOKEN"
        echo -e "${YELLOW}  ⚠${NC}  Could not mint a new pentester token, reusing existing PENTESTER_TOKEN"
    else
        ACTIVE_PENTESTER_TOKEN="$GITLAB_ADMIN_TOKEN"
        echo -e "${YELLOW}  ⚠${NC}  Could not mint pentester token, falling back to admin token for tooling"
    fi

    # Create pipeleek config directory
    docker exec pentester mkdir -p /root/.config/pipeleek 2>/dev/null || true

    # Create pipeleek config with runtime token (using docker exec directly)
    # Note: Use /root/.config/pipeleek/pipeleek.yaml as this is what pipeleek expects
    docker exec -T pentester bash -c "echo 'gitlab:' > /root/.config/pipeleek/pipeleek.yaml && echo '  url: http://gitlab' >> /root/.config/pipeleek/pipeleek.yaml && echo \"  token: $ACTIVE_PENTESTER_TOKEN\" >> /root/.config/pipeleek/pipeleek.yaml" 2>/dev/null || true

    # Set proper permissions
    docker exec pentester chmod 600 /root/.config/pipeleek/pipeleek.yaml 2>/dev/null || true

    # Update bashrc with credentials (no banner - shown by make pentester-shell)
    docker exec pentester bash -c "cat >> ~/.bashrc << 'BASHRC'

# GitLab Lab Credentials
export GITLAB_URL=\"http://gitlab\"
export PENTESTER_USER=\"pentester\"
export PENTESTER_PASSWORD=\"SecureP3nt3st3r@2024!\"
BASHRC" 2>/dev/null || true

    echo -e "${GREEN}✓${NC} Pentester container configured with pipeleek"
fi
echo ""

# Final summary
if [ $ERROR_COUNT -eq 0 ] && [ $WARN_COUNT -eq 0 ]; then
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  Setup Complete! 🎉                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}✓ All services running${NC}"
    echo -e "${GREEN}✓ GitLab populated with lab data${NC}"
    echo -e "${GREEN}✓ Pentester container ready${NC}"
else
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║            Setup Complete with Warnings ⚠                      ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}✓ All services running${NC}"
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠ GitLab populated with ${ERROR_COUNT} errors and ${WARN_COUNT} warnings${NC}"
    else
        echo -e "${YELLOW}⚠ GitLab populated with ${WARN_COUNT} warnings${NC}"
    fi
    echo -e "${GREEN}✓ Pentester container ready${NC}"
fi

# Option to enter pentester shell (only if container is running)
if docker exec pentester true 2>/dev/null; then
    read -p "Enter pentester container now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Entering pentester container...${NC}"
        docker-compose exec -it pentester /bin/bash
    fi
else
    echo -e "${YELLOW}⚠ Pentester container is not running.${NC}"
    echo "  You can enter it later with: docker-compose exec -it pentester /bin/bash"
fi
