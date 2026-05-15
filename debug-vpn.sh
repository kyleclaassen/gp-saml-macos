#!/bin/bash
# VPN Debug Script - Captures routing and network information
# This helps diagnose GlobalProtect VPN connection issues on macOS

set -e

LOGFILE="vpn-debug-$(date +%Y%m%d-%H%M%S).log"

echo "=== GlobalProtect VPN Debug Information ===" | tee "$LOGFILE"
echo "Date: $(date)" | tee -a "$LOGFILE"
echo "User: $(whoami)" | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# System Information
echo "=== System Information ===" | tee -a "$LOGFILE"
sw_vers | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# Network Interfaces Before Connection
echo "=== Network Interfaces (Before) ===" | tee -a "$LOGFILE"
ifconfig | grep -E "^[a-z]|inet " | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# Routing Table Before Connection
echo "=== Routing Table (Before) ===" | tee -a "$LOGFILE"
netstat -rn | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# DNS Configuration Before
echo "=== DNS Configuration (Before) ===" | tee -a "$LOGFILE"
scutil --dns | grep -A 1 "nameserver" | head -20 | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# Default Gateway
echo "=== Default Gateway ===" | tee -a "$LOGFILE"
route -n get default | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# Active Network Services
echo "=== Active Network Services ===" | tee -a "$LOGFILE"
networksetup -listallnetworkservices | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# Check for existing VPN connections
echo "=== Existing VPN Connections ===" | tee -a "$LOGFILE"
ifconfig | grep -E "^(utun|ppp|tun)" || echo "None found" | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# OpenConnect Version
echo "=== OpenConnect Version ===" | tee -a "$LOGFILE"
openconnect --version 2>&1 | head -3 | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# Check for vpnc-script
echo "=== vpnc-script Locations ===" | tee -a "$LOGFILE"
for path in /usr/local/etc/vpnc/vpnc-script /etc/vpnc/vpnc-script /opt/homebrew/etc/vpnc/vpnc-script; do
    if [ -f "$path" ]; then
        echo "Found: $path ($(wc -l < "$path") lines)" | tee -a "$LOGFILE"
        ls -l "$path" | tee -a "$LOGFILE"
    else
        echo "Not found: $path" | tee -a "$LOGFILE"
    fi
done
echo "" | tee -a "$LOGFILE"

# Check for custom scripts
echo "=== Custom VPN Scripts in Current Directory ===" | tee -a "$LOGFILE"
ls -l *.sh 2>/dev/null | tee -a "$LOGFILE" || echo "None found" | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

echo "=== Debug Information Saved ===" | tee -a "$LOGFILE"
echo "Log file: $LOGFILE"
echo ""
echo "Please review this file before sharing to ensure no sensitive data is included."
echo ""
echo "To connect with debug output, run:"
echo "  sudo openconnect --protocol=gp --script=./vpnc-script-macos.sh \\"
echo "    --verbose [YOUR_VPN_SERVER]"
