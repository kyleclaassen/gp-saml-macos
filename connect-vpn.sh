#!/bin/bash
# Wrapper script for GlobalProtect SAML authentication + VPN connection
# Usage: ./connect-vpn.sh <vpn-server> [-- extra-openconnect-args]
#
# This performs SAML auth via gp_saml_selenium.py before calling OpenConnect.
# Calling openconnect directly (without SAML pre-auth) fails because the server
# returns a SAML challenge that openconnect's XML parser cannot handle.

set -e

VPN_SERVER="${1:-}"
shift || true

if [ -z "$VPN_SERVER" ]; then
    echo "Usage: $0 <vpn-server> [-- extra-openconnect-args]"
    echo ""
    echo "Examples:"
    echo "  $0 vpn.company.com"
    echo "  $0 vpn.company.com -- --csd-wrapper=hip-report.sh"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GlobalProtect VPN Connection ===${NC}"
echo "Server: $VPN_SERVER"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v openconnect >/dev/null 2>&1; then
    echo -e "${RED}Error: openconnect not found${NC}"
    echo "Install with: brew install openconnect"
    exit 1
fi
echo "✓ OpenConnect found: $(which openconnect)"

# Determine Python runner (prefer uv for dependency isolation)
if command -v uv >/dev/null 2>&1; then
    PYTHON_CMD="uv run python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}Error: neither uv nor python3 found${NC}"
    exit 1
fi
echo "✓ Python runner: $PYTHON_CMD"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$SCRIPT_DIR/gp_saml_selenium.py" ]; then
    echo -e "${RED}Error: gp_saml_selenium.py not found${NC}"
    echo "Please run this script from the project directory"
    exit 1
fi
echo "✓ SAML authenticator found"

if [ ! -f "$SCRIPT_DIR/vpnc-script-macos.sh" ]; then
    echo -e "${RED}Error: vpnc-script-macos.sh not found${NC}"
    echo "Please run this script from the project directory"
    exit 1
fi
echo "✓ Custom vpnc-script found"

# Make scripts executable
chmod +x "$SCRIPT_DIR/vpnc-script-macos.sh"
chmod +x "$SCRIPT_DIR/debug-vpn.sh"

if [ "$(id -u)" -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}Note: OpenConnect requires root privileges${NC}"
    echo "You will be prompted for your password after SAML login"
    echo ""
fi

# Collect debug info
echo ""
echo -e "${YELLOW}Collecting pre-connection debug info...${NC}"
"$SCRIPT_DIR/debug-vpn.sh"

echo ""
echo -e "${GREEN}=== Starting SAML Authentication ===${NC}"
echo ""
echo "Steps:"
echo "  1. A browser window will open for SAML login"
echo "  2. Complete authentication in the browser"
echo "  3. Credentials are extracted automatically"
echo "  4. OpenConnect is launched with the SAML cookie"
echo ""
echo "Log files:"
echo "  - /tmp/vpnc-script-macos.log (routing script log)"
echo "  - vpn-debug-*.log (pre-connection network snapshot)"
echo ""
echo -e "${YELLOW}Press Ctrl+C to cancel, or Enter to continue...${NC}"
read -r

# Enable vpnc-script debug logging
export OPENCONNECT_DEBUG=1
export OPENCONNECT_LOG="/tmp/vpnc-script-macos.log"
> "$OPENCONNECT_LOG"

# Perform SAML authentication and connect.
# --gateway: use ssl-vpn/prelogin.esp (change to --portal for portal auth)
# --sudo: run openconnect under sudo after auth succeeds
# "$@": forward any extra args (e.g. -- --csd-wrapper=hip-report.sh)
cd "$SCRIPT_DIR"
$PYTHON_CMD gp_saml_selenium.py \
    --gateway \
    --sudo \
    "$VPN_SERVER" \
    "$@"

# After disconnect
echo ""
echo -e "${GREEN}=== Connection Closed ===${NC}"
echo ""
echo "Debug logs available at:"
echo "  - $OPENCONNECT_LOG"
LATEST_DEBUG=$(ls -t "$SCRIPT_DIR"/vpn-debug-*.log 2>/dev/null | head -1)
if [ -n "$LATEST_DEBUG" ]; then
    echo "  - $LATEST_DEBUG"
fi
