# Troubleshooting VPN Routing Issues on macOS

## Problem: Routing Errors on macOS

If you see errors like:
```
route: writing to routing socket: Can't assign requested address
add net 192.0.2.100: gateway 192.0.2.100: Can't assign requested address
is not a recognized network service.
```

These are common macOS routing issues with GlobalProtect VPN.

## Quick Fix

### Option 1: Use the Custom vpnc-script (Recommended)

The project includes a macOS-optimized routing script that handles these errors gracefully:

```bash
# Using gp_saml_selenium.py (automatically uses custom script)
uv run python3 gp_saml_selenium.py --gateway YOUR_SERVER --sudo

# Or manually with OpenConnect
sudo openconnect --protocol=gp \
  --script=./vpnc-script-macos.sh \
  YOUR_SERVER
```

### Option 2: Use the Debug Wrapper

Run the connection through the debug wrapper to see detailed routing information:

```bash
./connect-vpn.sh YOUR_SERVER
```

This will:
1. Collect pre-connection network info
2. Use the custom vpnc-script with logging
3. Save debug logs for analysis

## Understanding the Errors

### 1. "Can't assign requested address"

**Cause**: macOS is trying to add a route that conflicts with existing routes or uses the VPN IP as both source and gateway.

**Solution**: The custom vpnc-script handles this by:
- Checking if routes already exist before adding
- Using proper gateway addressing
- Gracefully handling errors without failing the connection

### 2. "is not a recognized network service"

**Cause**: The DNS configuration command can't find the active network service name.

**Solution**: The custom script auto-detects the active network service:
```bash
networksetup -listallnetworkservices | grep -v "^An asterisk"
```

### 3. Default Route Issues

**Cause**: Multiple default routes or conflicts with existing routing.

**Solution**: The custom script:
- Saves the original default gateway
- Properly restores it on disconnect
- Uses split-tunnel when available

## Debug Information Collection

Run the debug script to collect network information:

```bash
./debug-vpn.sh
```

This creates a log file with:
- Network interfaces and their IPs
- Current routing table
- DNS configuration
- Active network services
- vpnc-script locations

**Important**: Review the log file before sharing - it may contain network details.

## Manual Debugging Steps

### 1. Check Network Interfaces Before Connection

```bash
ifconfig | grep -E "^[a-z]|inet "
```

Save the output to compare after connection.

### 2. Check Routing Table Before Connection

```bash
netstat -rn
```

Note your default gateway.

### 3. Find Active Network Service

```bash
# List all network services
networksetup -listallnetworkservices

# Find active service with IP
for service in $(networksetup -listallnetworkservices | grep -v "^An"); do
  echo "=== $service ==="
  networksetup -getinfo "$service"
done
```

### 4. Test with Custom Script and Verbose Logging

```bash
# Enable debug mode
export OPENCONNECT_DEBUG=1
export OPENCONNECT_LOG=/tmp/vpn-routing.log

# Connect with verbose output
sudo openconnect --protocol=gp \
  --script=./vpnc-script-macos.sh \
  --verbose \
  YOUR_SERVER

# Check the logs
tail -f /tmp/vpn-routing.log
```

### 5. After Connection, Verify Routes

```bash
# Check if VPN interface is up
ifconfig | grep utun

# Check routing table
netstat -rn | grep utun

# Check DNS
scutil --dns | grep nameserver
```

## Common Issues and Solutions

### Issue: VPN connects but no internet

**Cause**: Routing not properly configured.

**Check**:
```bash
# Test VPN route
ping -c 3 10.0.1.0  # Use an internal IP from your VPN

# Test internet route
ping -c 3 8.8.8.8

# Check default route
netstat -rn | grep default
```

**Solution**: Use the custom vpnc-script which properly handles split-tunnel vs full-tunnel.

### Issue: DNS not working

**Cause**: DNS servers not configured on the active network service.

**Check**:
```bash
scutil --dns
```

**Solution**: The custom script auto-detects the active service and configures DNS properly.

### Issue: Routes disappear after a while

**Cause**: macOS might be reverting routes when the network changes.

**Solution**: Use `--reconnect-timeout` with OpenConnect:
```bash
sudo openconnect --protocol=gp \
  --script=./vpnc-script-macos.sh \
  --reconnect-timeout=30 \
  YOUR_SERVER
```

### Issue: "Operation not permitted" errors

**Cause**: Insufficient permissions or System Integrity Protection (SIP) restrictions.

**Solution**:
1. Make sure you're using `sudo`
2. Check script permissions: `ls -l vpnc-script-macos.sh`
3. Should show: `-rwxr-xr-x` (executable)

## HIP Report Warning

If you see:
```
WARNING: Server asked us to submit HIP report with md5sum...
VPN connectivity may be disabled or limited without HIP report submission.
```

This is informational. Your server requires HIP (Host Information Profile) reporting. The VPN will still work, but some resources might be restricted.

**To submit HIP reports**, use a wrapper script:
```bash
sudo openconnect --protocol=gp \
  --csd-wrapper=./hip-report.sh \
  --script=./vpnc-script-macos.sh \
  YOUR_SERVER
```

## Environment Variables for Debugging

Set these before connecting:

```bash
# Enable vpnc-script debug logging
export OPENCONNECT_DEBUG=1
export OPENCONNECT_LOG=/tmp/vpn-debug.log

# Then connect
./connect-vpn.sh YOUR_SERVER

# View logs in real-time
tail -f /tmp/vpn-debug.log
```

## Testing the Custom Script

To verify the custom script works correctly:

```bash
# Test syntax
bash -n vpnc-script-macos.sh
echo "Syntax: $?"  # Should be 0

# Test with dry-run (won't actually modify routing)
reason=connect \
TUNDEV=utun99 \
INTERNAL_IP4_ADDRESS=192.0.2.100 \
VPNGATEWAY=10.1.0.117 \
bash -x vpnc-script-macos.sh
```

## Configuration File

Create `~/.openconnect-config` for persistent settings:

```bash
# OpenConnect configuration
protocol=gp
script=/path/to/vpnc-script-macos.sh
verbose
reconnect-timeout=30
```

Then connect with:
```bash
sudo openconnect --config=~/.openconnect-config YOUR_SERVER
```

## Still Having Issues?

1. **Collect full debug info**:
   ```bash
   ./debug-vpn.sh > pre-connection.log
   # Connect to VPN
   ./debug-vpn.sh > post-connection.log
   diff pre-connection.log post-connection.log
   ```

2. **Check OpenConnect version**:
   ```bash
   openconnect --version
   # Should be 8.x or newer for GlobalProtect
   ```

3. **Try the standard vpnc-script**:
   ```bash
   # Install via Homebrew
   brew install vpnc-scripts
   
   # Use it
   sudo openconnect --protocol=gp \
     --script=/opt/homebrew/etc/vpnc/vpnc-script \
     YOUR_SERVER
   ```

4. **Report issues**: Include:
   - macOS version: `sw_vers`
   - OpenConnect version: `openconnect --version`
   - Debug log from `./debug-vpn.sh`
   - VPN routing log from `/tmp/vpn-routing.log`
   - **Remove any personal information before sharing**

## Security Note

The routing errors you're seeing are **not preventing the VPN connection** - the ESP tunnel is established successfully. The errors are mainly cosmetic and related to route management. Your VPN traffic is still encrypted and routed properly.

However, some specific resources might not be accessible if their routes failed to install. Check the logs to see which routes succeeded vs failed.
