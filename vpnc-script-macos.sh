#!/bin/bash
# Enhanced vpnc-script for macOS with better error handling and logging
# This is a simplified version that handles routing more gracefully on macOS
#
# Based on vpnc-script but optimized for macOS GlobalProtect connections
# Usage: openconnect --script=./vpnc-script-macos.sh ...

set -e
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Configuration
LOG_FILE="${OPENCONNECT_LOG:-/tmp/vpnc-script-macos.log}"
DEBUG="${OPENCONNECT_DEBUG:-0}"

# Logging function
log() {
    if [ "$DEBUG" = "1" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
    fi
}

log "=== vpnc-script called with reason: ${reason:-unknown} ==="
log "VPNGATEWAY=$VPNGATEWAY"
log "TUNDEV=$TUNDEV"
log "INTERNAL_IP4_ADDRESS=$INTERNAL_IP4_ADDRESS"
log "INTERNAL_IP4_MTU=$INTERNAL_IP4_MTU"
log "INTERNAL_IP4_DNS=$INTERNAL_IP4_DNS"

# Store original default gateway
if [ -z "$DEFAULT_GATEWAY" ]; then
    DEFAULT_GATEWAY=$(route -n get default 2>/dev/null | awk '/gateway:/ {print $2}')
    log "Original default gateway: $DEFAULT_GATEWAY"
fi

# Function to safely add route
add_route() {
    local network=$1
    local gateway=$2
    local netmask=${3:-255.255.255.255}
    
    log "Adding route: $network via $gateway (netmask: $netmask)"
    
    # Check if route already exists
    if route -n get "$network" 2>/dev/null | grep -q "route to: $network"; then
        log "Route to $network already exists, deleting first"
        route -q delete "$network" 2>/dev/null || true
    fi
    
    # Add the route with error handling
    if ! route -q add "$network" "$gateway" 2>/dev/null; then
        log "WARNING: Could not add route $network via $gateway"
        return 1
    fi
    
    return 0
}

# Function to configure DNS on macOS
configure_dns() {
    local service="$1"
    shift
    local dns_servers="$@"
    
    log "Configuring DNS for service: $service"
    log "DNS servers: $dns_servers"
    
    # Get the primary network service (usually Wi-Fi or Ethernet)
    if [ -z "$service" ]; then
        # Try to find the active service
        service=$(networksetup -listallnetworkservices | grep -v "^An asterisk" | head -1)
        log "Auto-detected network service: $service"
    fi
    
    if [ -n "$service" ]; then
        # Set DNS servers
        if networksetup -setdnsservers "$service" $dns_servers 2>&1 | tee -a "$LOG_FILE"; then
            log "DNS configured successfully"
        else
            log "WARNING: Could not configure DNS"
        fi
    else
        log "WARNING: Could not determine network service for DNS configuration"
    fi
}

case "$reason" in
    pre-init)
        log "Pre-init phase"
        ;;
        
    connect)
        log "=== Connect phase ==="
        
        # Configure tunnel interface
        if [ -n "$TUNDEV" ]; then
            log "Configuring tunnel interface: $TUNDEV"
            
            # Set IP address
            if [ -n "$INTERNAL_IP4_ADDRESS" ]; then
                log "Setting IP: $INTERNAL_IP4_ADDRESS"
                ifconfig "$TUNDEV" "$INTERNAL_IP4_ADDRESS" "$INTERNAL_IP4_ADDRESS" netmask 255.255.255.255 up
            fi
            
            # Set MTU if specified
            if [ -n "$INTERNAL_IP4_MTU" ]; then
                log "Setting MTU: $INTERNAL_IP4_MTU"
                ifconfig "$TUNDEV" mtu "$INTERNAL_IP4_MTU"
            fi
        fi
        
        # Add host route to VPN gateway via original gateway
        if [ -n "$VPNGATEWAY" ] && [ -n "$DEFAULT_GATEWAY" ]; then
            log "Adding host route to VPN gateway"
            add_route "$VPNGATEWAY" "$DEFAULT_GATEWAY" || log "WARNING: Could not add gateway route"
        fi
        
        # Add routes for split-tunnel networks
        if [ -n "$CISCO_SPLIT_INC" ]; then
            log "Configuring split-tunnel routes ($CISCO_SPLIT_INC networks)"
            
            i=0
            while [ $i -lt "$CISCO_SPLIT_INC" ]; do
                eval network="\$CISCO_SPLIT_INC_${i}_ADDR"
                eval netmask="\$CISCO_SPLIT_INC_${i}_MASK"
                eval netmasklen="\$CISCO_SPLIT_INC_${i}_MASKLEN"
                
                if [ -n "$network" ]; then
                    log "Adding split route $i: $network/$netmasklen"
                    add_route "$network" "$INTERNAL_IP4_ADDRESS" "$netmask" || true
                fi
                
                i=$((i + 1))
            done
        else
            log "No split-tunnel configuration, may use full tunnel"
            
            # For full tunnel, add default route via VPN
            if [ -n "$INTERNAL_IP4_ADDRESS" ]; then
                log "Setting default route via VPN"
                # Delete existing default route
                route -q delete default 2>/dev/null || true
                # Add new default via tunnel
                add_route default "$INTERNAL_IP4_ADDRESS" || log "WARNING: Could not set default route"
            fi
        fi
        
        # Configure DNS
        if [ -n "$INTERNAL_IP4_DNS" ]; then
            # Try to detect the active network service
            ACTIVE_SERVICE=$(networksetup -listallnetworkservices | grep -v "^An asterisk" | \
                while read -r service; do
                    if networksetup -getinfo "$service" | grep -q "^IP address:"; then
                        echo "$service"
                        break
                    fi
                done)
            
            configure_dns "$ACTIVE_SERVICE" $INTERNAL_IP4_DNS
        fi
        
        log "=== Connect phase complete ==="
        ;;
        
    disconnect)
        log "=== Disconnect phase ==="
        
        # Restore original default gateway
        if [ -n "$DEFAULT_GATEWAY" ]; then
            log "Restoring default gateway: $DEFAULT_GATEWAY"
            route -q delete default 2>/dev/null || true
            route -q add default "$DEFAULT_GATEWAY" 2>/dev/null || log "WARNING: Could not restore default gateway"
        fi
        
        # Restore DNS (remove VPN DNS servers)
        if [ -n "$INTERNAL_IP4_DNS" ]; then
            ACTIVE_SERVICE=$(networksetup -listallnetworkservices | grep -v "^An asterisk" | head -1)
            if [ -n "$ACTIVE_SERVICE" ]; then
                log "Restoring DNS for: $ACTIVE_SERVICE"
                networksetup -setdnsservers "$ACTIVE_SERVICE" "Empty" 2>/dev/null || true
            fi
        fi
        
        log "=== Disconnect phase complete ==="
        ;;
        
    reconnect)
        log "Reconnect requested"
        ;;
        
    *)
        log "Unknown reason: $reason"
        ;;
esac

exit 0
