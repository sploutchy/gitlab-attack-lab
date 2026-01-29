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
docker-compose up -d > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Services started"
echo ""

# Step 2: Wait for GitLab to be healthy
echo -e "${YELLOW}[STEP 2]${NC} Waiting for GitLab to initialize (this may take 3-5 minutes)..."
MAX_ATTEMPTS=60
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/api/v4/version" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
        echo -e "${GREEN}✓${NC} GitLab is ready"
        break
    fi
    
    # Show progress
    if [ $((ATTEMPT % 10)) -eq 0 ]; then
        echo -e "  Waiting... (${ATTEMPT}s)"
    fi
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}✗${NC} GitLab failed to initialize"
    exit 1
fi
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
    "user = User.find_by(username: 'root'); token = user.personal_access_tokens.create!(scopes: [:api, :read_user, :read_api, :read_repository, :write_repository, :admin_mode, :sudo], name: 'lab-admin-token', expires_at: 1.year.from_now); puts token.token" 2>&1)

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

# Run the populator and capture runner tokens
POPULATE_OUTPUT=$(python3 "$PROJECT_ROOT/scripts/populate-gitlab.py" "$PROJECT_ROOT/lab-config/structure.yml" "http://127.0.0.1" "$GITLAB_ADMIN_TOKEN" 2>&1)
POPULATE_EXIT=$?

echo "$POPULATE_OUTPUT" | grep -v "^===" | grep -v "="

if [ $POPULATE_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} GitLab structure populated"
    
    # Extract and save runner tokens to .env
    if echo "$POPULATE_OUTPUT" | grep -q "=== RUNNER_TOKENS ==="; then
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
        
        # Restart runner containers to pick up new tokens
        echo -e "  Restarting runner containers..."
        docker-compose restart gitlab-runner-docker gitlab-runner-shell > /dev/null 2>&1
        echo -e "${GREEN}  ✓${NC} Runner containers restarted"
    fi
else
    echo -e "${RED}✗${NC} Failed to populate GitLab structure"
    exit 1
fi
echo ""

# Step 5: Configure pentester container
echo -e "${YELLOW}[STEP 5]${NC} Configuring pentester container..."

# Create pipeleek config directory
docker exec pentester mkdir -p /root/.config/pipeleek 2>/dev/null || true

# Create pipeleek config with actual token (using docker exec directly)
# Note: Use /root/.config/pipeleek/pipeleek.yaml as this is what pipeleek expects
docker exec -T pentester bash -c "echo 'gitlab:' > /root/.config/pipeleek/pipeleek.yaml && echo '  url: http://gitlab' >> /root/.config/pipeleek/pipeleek.yaml && echo \"  token: $GITLAB_ADMIN_TOKEN\" >> /root/.config/pipeleek/pipeleek.yaml" 2>/dev/null || true

# Set proper permissions
docker exec pentester chmod 600 /root/.config/pipeleek/pipeleek.yaml 2>/dev/null || true

# Update bashrc with credentials
docker exec pentester bash -c "cat >> ~/.bashrc << 'BASHRC'

# GitLab Lab Credentials
export GITLAB_URL=\"http://gitlab\"
export GITLAB_USER=\"root\"
export GITLAB_PASSWORD=\"R00t@L4b_Adm1n_2024\"
export PENTESTER_USER=\"pentester\"
export PENTESTER_PASSWORD=\"SecureP3nt3st3r@2024!\"

# Welcome message
echo \"╔════════════════════════════════════════════════════╗\"
echo \"║     GitLab Attack Lab - Pentester Container        ║\"
echo \"╚════════════════════════════════════════════════════╝\"
echo \"\"
echo \"Configured credentials:\"
echo \"  GitLab URL:      \$GITLAB_URL\"
echo \"  Root User:       \$GITLAB_USER\"
echo \"  Root Password:   \$GITLAB_PASSWORD\"
echo \"  Pentester User:  \$PENTESTER_USER\"
echo \"  Pentester Pass:  \$PENTESTER_PASSWORD\"
echo \"\"
echo \"Try: pipeleek gl enum\"
echo \"\"
BASHRC" 2>/dev/null || true

echo -e "${GREEN}✓${NC} Pentester container configured with pipeleek"
echo ""

# Final summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  Setup Complete! 🎉                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ All services running${NC}"
echo -e "${GREEN}✓ GitLab populated with lab data${NC}"
echo -e "${GREEN}✓ Pentester container ready${NC}"
echo ""
echo -e "${YELLOW}Access GitLab:${NC}"
echo "  URL:      http://127.0.0.1"
echo "  Username: root"
echo "  Password: R00t@L4b_Adm1n_2024"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Open GitLab in your browser: http://127.0.0.1"
echo "  2. Enter the pentester shell: docker-compose exec pentester /bin/bash"
echo "  3. Run Pipeleek commands to explore the lab"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  # View services"
echo "  docker-compose ps"
echo ""
echo "  # View logs"
echo "  docker-compose logs -f gitlab"
echo ""
echo "  # Stop everything"
echo "  docker-compose down"
echo ""
echo "  # Stop and remove all data"
echo "  docker-compose down -v"
echo ""

# Option to enter pentester shell
read -p "Enter pentester container now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Entering pentester container...${NC}"
    docker-compose exec pentester /bin/bash
fi
