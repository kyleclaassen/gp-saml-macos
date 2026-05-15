# Quick Reference Guide

## Usage Examples

### Using gp_saml_selenium.py (Recommended)

```bash
# Authenticate and connect (uses custom routing script automatically)
uv run python3 gp_saml_selenium.py \
  --gateway vpn.example.com \
  --clientos=Windows \
  --sudo
```

### Using OpenConnect Directly

```bash
# After getting credentials from gp_saml_selenium.py --print-only
echo 'YOUR_COOKIE' | sudo openconnect \
  --protocol=gp \
  --user='YOUR_USERNAME' \
  --os=win \
  --usergroup=gateway:prelogin-cookie \
  --passwd-on-stdin \
  vpn.example.com
```

### Using the Debug Wrapper

For troubleshooting routing issues:

```bash
# This will show you exactly what's happening with routing
./connect-vpn.sh vpn.example.com
```

## Understanding Your VPN Connection

Based on your output, here's what's happening:

### ✅ What's Working

1. **SAML Authentication**: Successfully authenticating via ADFS
2. **ESP Tunnel**: ESP tunnel establishes successfully
3. **IP Assignment**: You get IP `192.0.2.100`
4. **Session**: Valid for ~24 hours

### ⚠️ What Needs Attention

1. **Routing Errors**: Some routes can't be added (cosmetic, doesn't break VPN)
2. **HIP Report**: Server wants HIP report (informational warning)
3. **Network Service**: DNS configuration script can't find service name

### 🔧 The Routing Errors Explained

```
route: writing to routing socket: Can't assign requested address
```
- **Cause**: macOS doesn't like adding route where destination = gateway
- **Impact**: Minimal - VPN still works
- **Fix**: Custom vpnc-script handles this gracefully

```
is not a recognized network service.
```
- **Cause**: DNS script can't find active network service
- **Impact**: DNS might not update properly
- **Fix**: Custom script auto-detects the service

## Quick Troubleshooting

### Check VPN Status

```bash
# Is VPN interface up?
ifconfig | grep utun

# Are routes installed?
netstat -rn | grep 172.30

# Is DNS configured?
scutil --dns | head -20
```

### Test Connectivity

```bash
# Test internal network (your VPN network)
ping 10.0.1.0

# Test specific internal server
ping 10.1.0.9

# Test internet (should still work)
ping 8.8.8.8
```

### View Debug Logs

```bash
# Pre-connection info
./debug-vpn.sh

# Connection logs (while connected)
tail -f /tmp/vpnc-script-macos.log
```

## Common Workflows

### 1. Daily Connection

```bash
# Quick connect
uv run python3 gp_saml_selenium.py --gateway vpn.example.com --sudo
```

### 2. Debug Connection Issues

```bash
# Collect debug info and connect with logging
./connect-vpn.sh vpn.example.com

# Review logs
cat /tmp/vpnc-script-macos.log
```

### 3. Just Get Credentials (No Connect)

```bash
# For manual use or scripting
uv run python3 gp_saml_selenium.py \
  --gateway vpn.example.com \
  --print-only
```

### 4. Headless Mode (If You Set Up Auto-Login)

```bash
# No browser window (requires SSO auto-login configured)
uv run python3 gp_saml_selenium.py \
  --gateway vpn.example.com \
  --headless \
  --sudo
```

## Your VPN Routes

Based on your output, these routes are being configured:

### Microsoft Office 365 Routes
- `52.120.0.0/14` → Office 365 services
- `52.112.0.0/14` → Office 365 services  
- `13.107.64.0/18` → Microsoft services

### Internal University Routes
- `10.1.0.6/32` → Internal server
- `10.1.0.9/32` → Internal server
- `10.1.0.8/32` → Internal server
- `10.1.0.65/24` → Internal network
- `10.0.1.0/24` → Internal network
- `10.0.2.0/24` → Internal network

### Split Tunnel Configuration

Your VPN uses **split tunneling**, meaning:
- ✅ Internal university traffic goes through VPN
- ✅ Office 365 traffic goes through VPN
- ✅ Other internet traffic goes direct (not through VPN)

This is efficient and faster for general internet use.

## Environment Setup

Create an alias for easy connection:

```bash
# Add to ~/.zshrc or ~/.bashrc
alias vpn-connect='cd /path/to/gp-saml-macos && uv run python3 gp_saml_selenium.py --gateway vpn.example.com --sudo'
alias vpn-debug='cd /path/to/gp-saml-macos && ./connect-vpn.sh vpn.example.com'

# Then just run:
# vpn-connect
```

## Security Notes

1. **Credentials**: Never hardcoded - passed via stdin
2. **Cookies**: Stored only in memory during session
3. **Browser**: Uses clean profile, no persistence
4. **Logs**: May contain network info - review before sharing

## File Locations

```
Project Files:
├── gp_saml_selenium.py      # Main auth script
├── vpnc-script-macos.sh     # Custom routing (handles macOS quirks)
├── connect-vpn.sh           # Debug wrapper
├── debug-vpn.sh             # Network info collector
└── TROUBLESHOOTING.md       # Detailed troubleshooting guide

Generated Logs:
├── /tmp/vpnc-script-macos.log  # Routing script log
└── vpn-debug-*.log             # Network state snapshots
```

## Next Steps

1. **Try the custom script**:
   ```bash
   uv run python3 gp_saml_selenium.py --gateway vpn.example.com --sudo
   ```

2. **If issues persist**:
   ```bash
   ./connect-vpn.sh vpn.example.com
   ```

3. **Check the logs**:
   ```bash
   cat /tmp/vpnc-script-macos.log
   ```

4. **Test connectivity**:
   ```bash
   ping 10.0.1.0  # Internal network
   ping 8.8.8.8      # Internet
   ```

## Need Help?

See detailed troubleshooting in `TROUBLESHOOTING.md` or run:
```bash
./debug-vpn.sh
```

The routing errors you saw are **not critical** - they're known macOS routing quirks that don't prevent VPN functionality. The custom vpnc-script handles them gracefully.
