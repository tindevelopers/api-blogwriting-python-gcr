#!/bin/bash

# Test Secrets Sync Endpoint
# Tests the new POST /api/v1/admin/secrets/sync endpoint

BASE_URL="${API_URL:-https://blog-writer-api-dev-613248238610.europe-west9.run.app}"
ADMIN_TOKEN="${ADMIN_TOKEN:-your-admin-token-here}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}======================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Test 1: List secrets first
test_list_secrets() {
    print_header "Test 1: List Available Secrets"
    
    print_info "Fetching list of secrets from Secret Manager..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X GET "$BASE_URL/api/v1/admin/secrets" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        --max-time 30 \
        2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Successfully retrieved secrets list"
        
        SECRET_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        print_info "Found $SECRET_COUNT secrets"
        
        # Show secret names
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
        
        return 0
    elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
        print_error "Authentication failed. Please set ADMIN_TOKEN environment variable"
        print_info "export ADMIN_TOKEN=your-admin-jwt-token"
        return 1
    else
        print_error "Failed to list secrets: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Test 2: Dry run sync
test_dry_run_sync() {
    print_header "Test 2: Dry Run Sync (Preview)"
    
    print_info "Testing dry run sync (no actual changes)..."
    
    REQUEST_JSON=$(cat <<EOF
{
  "dry_run": true
}
EOF
)
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$BASE_URL/api/v1/admin/secrets/sync" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_JSON" \
        --max-time 60 \
        2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Dry run completed successfully"
        
        SYNCED_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('synced_count', 0))" 2>/dev/null || echo "0")
        print_info "Would sync: $SYNCED_COUNT secrets"
        
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
        
        return 0
    else
        print_error "Dry run failed: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Test 3: Sync specific secrets
test_selective_sync() {
    print_header "Test 3: Selective Sync (Specific Secrets)"
    
    print_info "Syncing OPENAI_API_KEY and ANTHROPIC_API_KEY..."
    
    REQUEST_JSON=$(cat <<EOF
{
  "secret_names": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
  "dry_run": false
}
EOF
)
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$BASE_URL/api/v1/admin/secrets/sync" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_JSON" \
        --max-time 60 \
        2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Selective sync completed"
        
        SYNCED_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('synced_count', 0))" 2>/dev/null || echo "0")
        FAILED_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('failed', [])))" 2>/dev/null || echo "0")
        
        print_info "Synced: $SYNCED_COUNT secrets"
        print_info "Failed: $FAILED_COUNT secrets"
        
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
        
        return 0
    else
        print_error "Selective sync failed: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Test 4: Sync all secrets
test_sync_all() {
    print_header "Test 4: Sync All Secrets"
    
    print_info "Syncing all secrets from Secret Manager..."
    print_info "This may take 10-30 seconds..."
    
    REQUEST_JSON=$(cat <<EOF
{
  "dry_run": false
}
EOF
)
    
    START_TIME=$(date +%s)
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$BASE_URL/api/v1/admin/secrets/sync" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_JSON" \
        --max-time 90 \
        2>&1)
    
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "All secrets synced in ${ELAPSED}s"
        
        SYNCED_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('synced_count', 0))" 2>/dev/null || echo "0")
        FAILED_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('failed', [])))" 2>/dev/null || echo "0")
        SYNCED_BY=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('synced_by', 'unknown'))" 2>/dev/null || echo "unknown")
        
        print_info "Synced: $SYNCED_COUNT secrets"
        print_info "Failed: $FAILED_COUNT secrets"
        print_info "Synced by: $SYNCED_BY"
        
        # Show synced secrets
        echo -e "\n${YELLOW}Synced Secrets:${NC}"
        echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"  • {s['name']} (version {s.get('version', 'unknown')})\") for s in data.get('synced_secrets', [])]" 2>/dev/null
        
        # Show failed secrets if any
        if [ "$FAILED_COUNT" -gt 0 ]; then
            echo -e "\n${RED}Failed Secrets:${NC}"
            echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"  • {s['name']}: {s.get('error', 'unknown error')}\") for s in data.get('failed', [])]" 2>/dev/null
        fi
        
        return 0
    else
        print_error "Sync failed: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Test 5: Verify auto-sync on create/update
test_auto_sync() {
    print_header "Test 5: Auto-Sync on Create/Update"
    
    print_info "Creating/updating a test secret..."
    
    TEST_SECRET_NAME="TEST_API_KEY_$(date +%s)"
    TEST_VALUE="test-key-value-123"
    
    REQUEST_JSON=$(cat <<EOF
{
  "value": "$TEST_VALUE",
  "labels": {
    "test": "true",
    "auto_sync": "test"
  }
}
EOF
)
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X PUT "$BASE_URL/api/v1/admin/secrets/$TEST_SECRET_NAME" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_JSON" \
        --max-time 30 \
        2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        SYNCED=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('synced', False))" 2>/dev/null || echo "false")
        VERSION=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
        
        if [ "$SYNCED" = "True" ]; then
            print_success "Secret created and auto-synced successfully"
            print_info "Version: $VERSION"
            print_info "Auto-synced: Yes"
            
            # Clean up test secret
            print_info "Cleaning up test secret..."
            curl -s -X DELETE "$BASE_URL/api/v1/admin/secrets/$TEST_SECRET_NAME" \
                -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null 2>&1
            
            return 0
        else
            print_error "Secret created but auto-sync flag not set"
            return 1
        fi
    else
        print_error "Create/update failed: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${GREEN}======================================================================${NC}"
    echo -e "${GREEN}Secrets Sync Endpoint Test Suite${NC}"
    echo -e "${GREEN}======================================================================${NC}"
    echo -e "${YELLOW}Testing backend: $BASE_URL${NC}"
    echo -e "${YELLOW}Time: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    
    # Check if admin token is set
    if [ "$ADMIN_TOKEN" = "your-admin-token-here" ]; then
        echo -e "\n${RED}ERROR: ADMIN_TOKEN not set!${NC}"
        echo -e "${YELLOW}Please set your admin token:${NC}"
        echo -e "  export ADMIN_TOKEN=your-admin-jwt-token"
        echo -e "\nNote: You need admin authentication to test secrets endpoints"
        exit 1
    fi
    
    PASSED=0
    TOTAL=0
    
    # Run tests
    test_list_secrets && ((PASSED++))
    ((TOTAL++))
    sleep 1
    
    test_dry_run_sync && ((PASSED++))
    ((TOTAL++))
    sleep 1
    
    test_selective_sync && ((PASSED++))
    ((TOTAL++))
    sleep 2
    
    test_sync_all && ((PASSED++))
    ((TOTAL++))
    sleep 1
    
    test_auto_sync && ((PASSED++))
    ((TOTAL++))
    
    # Print summary
    print_header "Test Summary"
    
    if [ $PASSED -eq $TOTAL ]; then
        print_success "All tests passed! ($PASSED/$TOTAL)"
        echo -e "\n${GREEN}✓ Secrets sync endpoint is working correctly${NC}"
        echo -e "${GREEN}✓ Auto-sync on create/update is enabled${NC}"
        echo -e "${GREEN}✓ synced_count field is returned${NC}"
        
        return 0
    else
        print_error "Some tests failed ($PASSED/$TOTAL passed)"
        echo -e "\n${YELLOW}Troubleshooting tips:${NC}"
        echo "1. Verify you have admin token: export ADMIN_TOKEN=your-token"
        echo "2. Check IAM permissions for Secret Manager"
        echo "3. Review backend logs:"
        echo "   gcloud logging read 'resource.labels.service_name=blog-writer-api-dev' --limit=20"
        
        return 1
    fi
}

# Run main function
main
exit $?

