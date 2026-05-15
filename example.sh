#!/bin/bash
# Example usage script for gp_saml_selenium.py

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}GlobalProtect SAML Authenticator - Example Usage${NC}\n"

# Check if server argument provided
if [ -z "$1" ]; then
    echo "Usage: $0 <vpn-server>"
    echo ""
    echo "Examples:"
    echo "  $0 vpn.company.com"
    echo "  $0 gateway.company.com"
    exit 1
fi

SERVER="$1"

echo -e "${GREEN}Step 1: Test authentication (print credentials only)${NC}"
echo "Command: python3 gp_saml_selenium.py --gateway $SERVER --print-only"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
python3 gp_saml_selenium.py --gateway "$SERVER" --print-only

echo ""
echo -e "${GREEN}Step 2: Connect to VPN with sudo${NC}"
echo "Command: python3 gp_saml_selenium.py --gateway $SERVER --sudo"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
python3 gp_saml_selenium.py --gateway "$SERVER" --sudo
