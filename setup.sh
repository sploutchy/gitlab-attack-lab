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

# Step 1: Start Docker Compose services
echo -e "${YELLOW}[STEP 1]${NC} Starting Docker Compose services..."
cd "$PROJECT_ROOT"
docker-compose up -d > /dev/null 2>&1 || true
echo -e "${GREEN}✓${NC} Services started"
echo ""

# Step 2: Wait for GitLab to be healthy
echo -e "${YELLOW}[STEP 2]${NC} Waiting for GitLab to initialize (this may take 5-10 minutes)..."
ATTEMPT=0
while true; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Try to access GitLab API - don't require container to be healthy, just accessible
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/api/v4/version" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
        echo -e "${GREEN}✓${NC} GitLab is ready (took ${ATTEMPT}s)"
        break
    fi
    
    # Show progress every 30 seconds
    if [ $((ATTEMPT % 30)) -eq 0 ]; then
        STATUS=$(docker-compose ps gitlab 2>/dev/null | tail -1 | awk '{print $NF}' || echo "unknown")
        echo -e "  Waiting... (${ATTEMPT}s elapsed) - Container: $STATUS"
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
        USER_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" "http://127.0.0.1/api/v4/user" 2>/dev/null || echo "000")
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
POPULATE_OUTPUT=$(python3 "$PROJECT_ROOT/scripts/populate-gitlab.py" "$MERGED_CONFIG" "http://127.0.0.1" "$GITLAB_ADMIN_TOKEN" 2>&1)
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
        
        # Wait for runners to register (up to 60 seconds)
        echo -e "  Waiting for runners to register and come online..."
        RUNNER_WAIT=0
        RUNNERS_FOUND=0
        while [ $RUNNER_WAIT -lt 60 ]; do
            REGISTERED=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
                "http://127.0.0.1/api/v4/runners/all" 2>/dev/null | grep -c '"status":"online"' 2>/dev/null || echo "0")
            
            # Clean up the variable to remove any whitespace/newlines
            REGISTERED=$(echo "$REGISTERED" | tr -d '\n' | tail -1)
            
            if [ "$REGISTERED" -ge 2 ] 2>/dev/null; then
                echo -e "${GREEN}  ✓${NC} Runners registered and online (${REGISTERED} runners)"
                RUNNERS_FOUND=1
                break
            fi
            
            sleep 2
            RUNNER_WAIT=$((RUNNER_WAIT + 2))
        done
        
        if [ "$RUNNERS_FOUND" -ne 1 ]; then
            echo -e "${YELLOW}  ⚠${NC}  Only ${REGISTERED} runners online (expected 2)"
            echo -e "${YELLOW}     Runners may take additional time to come online${NC}"
        fi
    fi
else
    echo -e "${RED}✗${NC} Failed to populate GitLab structure"
    exit 1
fi
echo ""

# Step 5: Configure pentester container
echo -e "${YELLOW}[STEP 5]${NC} Configuring pentester container..."

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
    # Create pipeleek config directory
    docker exec pentester mkdir -p /root/.config/pipeleek 2>/dev/null || true

    # Create pipeleek config with actual token (using docker exec directly)
    # Note: Use /root/.config/pipeleek/pipeleek.yaml as this is what pipeleek expects
    docker exec -T pentester bash -c "echo 'gitlab:' > /root/.config/pipeleek/pipeleek.yaml && echo '  url: http://gitlab' >> /root/.config/pipeleek/pipeleek.yaml && echo \"  token: $GITLAB_ADMIN_TOKEN\" >> /root/.config/pipeleek/pipeleek.yaml" 2>/dev/null || true

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
