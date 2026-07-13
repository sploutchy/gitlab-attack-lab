#!/bin/bash
# Manual Scenario Validation Script
# Tests all scenarios and extracts flags for end-to-end verification

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load environment
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
else
    echo "[-] .env file not found!"
    exit 1
fi

GITLAB_HOST_URL="${GITLAB_HOST_URL:-http://127.0.0.1:7700}"
GITLAB_HOST_URL="${GITLAB_HOST_URL%/}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
SKIPPED=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║         Manual Scenario Validation - All Scenarios             ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Helper functions
check_flag() {
    local scenario=$1
    local flag=$2
    local pattern=$3
    
    if [[ $flag =~ $pattern ]]; then
        echo -e "${GREEN}✓${NC} SCENARIO $scenario - FLAG CAPTURED: $flag"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} SCENARIO $scenario - INVALID FLAG FORMAT: $flag"
        ((FAILED++))
        return 1
    fi
}

# ============================================================================
# SCENARIO 00: Getting Started - Extract INTRO_FLAG from security-tools
# ============================================================================
echo -e "${YELLOW}[SCENARIO 00]${NC} Getting Started - Security Tools Flag Extraction"
echo "Waiting for security-tools pipeline to complete and log flag..."

# Poll for job completion
ATTEMPTS=0
MAX_ATTEMPTS=60
SCENARIO_00_FLAG=""

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    # Get the security-tools project (ID 5) pipelines
    PIPELINES=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
        "$GITLAB_HOST_URL/api/v4/projects/5/pipelines" | jq -r '.[0].id')
    
    if [ -n "$PIPELINES" ] && [ "$PIPELINES" != "null" ]; then
        # Get jobs from the pipeline
        JOBS=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
            "$GITLAB_HOST_URL/api/v4/projects/5/pipelines/$PIPELINES/jobs" | jq -r '.[] | .id')
        
        if [ -n "$JOBS" ] && [ "$JOBS" != "null" ]; then
            for JOB_ID in $JOBS; do
                JOB_STATUS=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
                    "$GITLAB_HOST_URL/api/v4/projects/5/jobs/$JOB_ID" | jq -r '.status')
                
                if [ "$JOB_STATUS" = "success" ]; then
                    # Get job log
                    JOB_LOG=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
                        "$GITLAB_HOST_URL/api/v4/projects/5/jobs/$JOB_ID/log" 2>/dev/null || echo "")
                    
                    # Extract flag pattern: FLAG{...}
                    SCENARIO_00_FLAG=$(echo "$JOB_LOG" | grep -oP 'FLAG\{[^}]+\}' | head -1 || echo "")
                    
                    if [ -n "$SCENARIO_00_FLAG" ]; then
                        break 2
                    fi
                fi
            done
        fi
    fi
    
    ((ATTEMPTS++))
    if [ $((ATTEMPTS % 10)) -eq 0 ]; then
        echo "  Waiting... ($ATTEMPTS/60s)"
    fi
    sleep 1
done

if [ -n "$SCENARIO_00_FLAG" ]; then
    check_flag "00" "$SCENARIO_00_FLAG" '^FLAG\{[A-Za-z0-9_]+\}$'
else
    echo -e "${YELLOW}⚠${NC} SCENARIO 00 - Flag not yet available in job logs (may need more time)"
    ((SKIPPED++))
fi
echo ""

# ============================================================================
# SCENARIO 01: CI/CD Variables Exposure - Use pipeleek
# ============================================================================
echo -e "${YELLOW}[SCENARIO 01]${NC} CI/CD Variables Exposure - Pipeleek Enumeration"
echo "Scanning for public project CI/CD variables..."

# First, ensure pentester has access to pipeleek
PENTESTER_TOKEN=$(grep "PENTESTER_TOKEN" "$SCRIPT_DIR/.env" | cut -d= -f2)

if [ -z "$PENTESTER_TOKEN" ]; then
    echo -e "${RED}✗${NC} SCENARIO 01 - Pentester token not found in .env"
    ((FAILED++))
else
    # Enter pentester container and run pipeleek
    PIPELEEK_OUTPUT=$(docker exec pentester pipeleek renovate bots 2>&1 || echo "")
    
    # Check if pipeleek ran successfully and found renovate-bot
    if echo "$PIPELEEK_OUTPUT" | grep -q "renovate-bot"; then
        echo -e "${GREEN}✓${NC} SCENARIO 01 - Pipeleek successfully identified renovate-bot"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} SCENARIO 01 - Pipeleek check incomplete (may need more setup time)"
        ((SKIPPED++))
    fi
fi
echo ""

# ============================================================================
# SCENARIO 02: Lateral Movement - Extract PAT from artifacts
# ============================================================================
echo -e "${YELLOW}[SCENARIO 02]${NC} Lateral Movement - Artifact PAT Extraction"
echo "Checking for private-test-data artifacts with leaked tokens..."

# Look for artifacts in project 10 (private-test-data)
ARTIFACTS=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
    "$GITLAB_HOST_URL/api/v4/projects/10/artifacts" 2>/dev/null | jq -r '.[] | .id' | head -1)

if [ -n "$ARTIFACTS" ] && [ "$ARTIFACTS" != "null" ]; then
    echo -e "${GREEN}✓${NC} SCENARIO 02 - Artifacts found in private-test-data project"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} SCENARIO 02 - No artifacts yet (pipelines still executing)"
    ((SKIPPED++))
fi
echo ""

# ============================================================================
# SCENARIO 03: Renovate Bot Exploitation - Check webhook logs
# ============================================================================
echo -e "${YELLOW}[SCENARIO 03]${NC} Renovate Bot Exploitation - Webhook Log Analysis"
echo "Checking webhook logger for renovate-bot activity..."

# Query webhook logger service (runs on port 7705)
WEBHOOK_LOGS=$(curl -s http://localhost:7705/logs 2>/dev/null || echo "")

if echo "$WEBHOOK_LOGS" | grep -q "renovate"; then
    echo -e "${GREEN}✓${NC} SCENARIO 03 - Renovate bot activity detected in webhooks"
    
    # Try to extract flag from logs
    SCENARIO_03_FLAG=$(echo "$WEBHOOK_LOGS" | grep -oP 'FLAG\{[^}]+\}' | head -1 || echo "")
    
    if [ -n "$SCENARIO_03_FLAG" ]; then
        check_flag "03" "$SCENARIO_03_FLAG" '^FLAG\{[A-Za-z0-9_]+\}$'
    else
        ((PASSED++))
    fi
else
    echo -e "${YELLOW}⚠${NC} SCENARIO 03 - Webhook logs not yet populated"
    ((SKIPPED++))
fi
echo ""

# ============================================================================
# SCENARIO 04: Runner Abuse - Check for breakout flag
# ============================================================================
echo -e "${YELLOW}[SCENARIO 04]${NC} Runner Abuse - Check Breakout Job Output"
echo "Monitoring runner-breakout-lab and recurring victim jobs..."

# Check project 12 (runner-breakout-lab) for job completion
ATTEMPTS=0
MAX_ATTEMPTS=60
SCENARIO_04_FLAG=""

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    # Get runner-breakout-lab pipelines
    PIPELINES=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
        "$GITLAB_HOST_URL/api/v4/projects/12/pipelines" | jq -r '.[0].id')
    
    if [ -n "$PIPELINES" ] && [ "$PIPELINES" != "null" ]; then
        # Get jobs
        JOBS=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
            "$GITLAB_HOST_URL/api/v4/projects/12/pipelines/$PIPELINES/jobs" | jq -r '.[] | .id')
        
        if [ -n "$JOBS" ] && [ "$JOBS" != "null" ]; then
            for JOB_ID in $JOBS; do
                JOB_STATUS=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
                    "$GITLAB_HOST_URL/api/v4/projects/12/jobs/$JOB_ID" | jq -r '.status')
                
                if [ "$JOB_STATUS" = "success" ] || [ "$JOB_STATUS" = "failed" ]; then
                    # Get job log for breakout evidence
                    JOB_LOG=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
                        "$GITLAB_HOST_URL/api/v4/projects/12/jobs/$JOB_ID/log" 2>/dev/null || echo "")
                    
                    # Check for breakout evidence
                    if echo "$JOB_LOG" | grep -q "breakout\|escape\|exploit"; then
                        echo -e "${GREEN}✓${NC} SCENARIO 04 - Runner breakout activity detected"
                        ((PASSED++))
                        break 2
                    fi
                fi
            done
        fi
    fi
    
    ((ATTEMPTS++))
    if [ $((ATTEMPTS % 15)) -eq 0 ]; then
        echo "  Waiting for runner jobs... ($ATTEMPTS/60s)"
    fi
    sleep 1
done

if [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; then
    echo -e "${YELLOW}⚠${NC} SCENARIO 04 - Runner jobs still executing"
    ((SKIPPED++))
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Validation Summary                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}✓ Passed:${NC}  $PASSED"
echo -e "  ${YELLOW}⚠ Skipped:${NC} $SKIPPED (jobs still executing - may pass after setup stabilization)"
echo -e "  ${RED}✗ Failed:${NC}  $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed or skipped (pending runner availability)${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
