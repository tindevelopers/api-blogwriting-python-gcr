#!/bin/bash
# Bulk Add Google Search Console Service Account Helper Script
# This script helps you quickly add the service account to multiple sites

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service Account Email
SERVICE_ACCOUNT_EMAIL="blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Google Search Console - Bulk Add Service Account Helper${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Service Account Email:${NC}"
echo -e "${YELLOW}${SERVICE_ACCOUNT_EMAIL}${NC}"
echo ""

# Check if sites file exists
SITES_FILE="gsc-sites.txt"

if [ ! -f "$SITES_FILE" ]; then
    echo -e "${YELLOW}Creating sites file: ${SITES_FILE}${NC}"
    echo "# Add your site URLs here, one per line" > "$SITES_FILE"
    echo "# Format: https://example.com or sc-domain:example.com" >> "$SITES_FILE"
    echo "# Example:" >> "$SITES_FILE"
    echo "# https://site1.com" >> "$SITES_FILE"
    echo "# https://site2.com" >> "$SITES_FILE"
    echo "# sc-domain:example.com" >> "$SITES_FILE"
    echo ""
    echo -e "${BLUE}Created ${SITES_FILE}. Please add your site URLs to this file.${NC}"
    echo ""
    read -p "Press Enter to open the file for editing..."
    
    # Try to open in editor
    if command -v nano &> /dev/null; then
        nano "$SITES_FILE"
    elif command -v vim &> /dev/null; then
        vim "$SITES_FILE"
    else
        echo "Please edit $SITES_FILE manually and add your site URLs."
    fi
fi

# Read sites from file
SITES=$(grep -v '^#' "$SITES_FILE" | grep -v '^$' | tr '\n' ' ')

if [ -z "$SITES" ]; then
    echo -e "${YELLOW}No sites found in ${SITES_FILE}. Please add site URLs.${NC}"
    exit 1
fi

echo -e "${BLUE}Found sites:${NC}"
echo "$SITES" | tr ' ' '\n' | nl
echo ""

# Generate direct links
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Direct Links to Add User Pages${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

COUNTER=1
for SITE in $SITES; do
    # URL encode the site URL
    ENCODED_SITE=$(echo "$SITE" | sed 's/:/%3A/g' | sed 's/\//%2F/g')
    
    # Generate direct link (approximate - GSC doesn't have direct add user links)
    echo -e "${BLUE}Site ${COUNTER}: ${SITE}${NC}"
    echo "1. Go to: https://search.google.com/search-console"
    echo "2. Select property: ${SITE}"
    echo "3. Go to: Settings → Users and permissions"
    echo "4. Click: Add user"
    echo "5. Email: ${SERVICE_ACCOUNT_EMAIL}"
    echo "6. Permission: Full"
    echo "7. Click: Add"
    echo ""
    
    COUNTER=$((COUNTER + 1))
done

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Quick Copy-Paste Instructions${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Service Account Email (copy this):${NC}"
echo -e "${GREEN}${SERVICE_ACCOUNT_EMAIL}${NC}"
echo ""
echo "Steps for each site:"
echo "1. Open Google Search Console"
echo "2. Select site property"
echo "3. Settings → Users and permissions"
echo "4. Add user → Paste email above → Full → Add"
echo ""

# Create checklist file
CHECKLIST_FILE="gsc-setup-checklist.txt"
echo "Google Search Console Setup Checklist" > "$CHECKLIST_FILE"
echo "Service Account: ${SERVICE_ACCOUNT_EMAIL}" >> "$CHECKLIST_FILE"
echo "" >> "$CHECKLIST_FILE"
echo "Sites to configure:" >> "$CHECKLIST_FILE"
COUNTER=1
for SITE in $SITES; do
    echo "[ ] ${COUNTER}. ${SITE}" >> "$CHECKLIST_FILE"
    COUNTER=$((COUNTER + 1))
done

echo ""
echo -e "${GREEN}✓ Checklist saved to: ${CHECKLIST_FILE}${NC}"
echo ""
echo -e "${BLUE}Tip:${NC} Open multiple browser tabs, one for each site, to speed up the process."
echo ""

# Ask if user wants to open GSC
read -p "Open Google Search Console in browser? (y/n): " OPEN_BROWSER
if [[ "$OPEN_BROWSER" == "y" || "$OPEN_BROWSER" == "Y" ]]; then
    if command -v open &> /dev/null; then
        open "https://search.google.com/search-console"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "https://search.google.com/search-console"
    else
        echo "Please open: https://search.google.com/search-console"
    fi
fi

echo ""
echo -e "${GREEN}Setup complete! Follow the instructions above to add the service account to each site.${NC}"

