# Installation and Setup Guide

## Quick Start

### 1. Install System Dependencies

**macOS:**
```bash
# Install OpenConnect VPN client
brew install openconnect

# Install Chrome or Chromium (if not already installed)
brew install --cask google-chrome
# OR
brew install chromium

# Install ChromeDriver
brew install chromedriver

# Fix macOS security warning for ChromeDriver
xattr -d com.apple.quarantine $(which chromedriver)
```

**Ubuntu/Debian:**
```bash
# Install OpenConnect
sudo apt update
sudo apt install openconnect

# Install Chromium and ChromeDriver
sudo apt install chromium-browser chromium-chromedriver

# Alternative: Install Chrome and ChromeDriver
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt install -f
```

**Fedora/RHEL:**
```bash
# Install OpenConnect
sudo dnf install openconnect

# Install Chromium and ChromeDriver
sudo dnf install chromium chromium-chromedriver
```

### 2. Install Python Dependencies

This project uses `uv` for dependency management. If you don't have it installed:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project dependencies:

```bash
# Install dependencies
uv sync

# Or install manually with pip
pip install requests selenium
```

### 3. Verify Installation

```bash
# Check if all dependencies are installed
uv run python3 validate.py

# Test the script help
uv run python3 gp_saml_selenium.py --help
```

## Running the Script

### Method 1: Using uv (Recommended)

```bash
# Print credentials only
uv run python3 gp_saml_selenium.py --gateway vpn.company.com --print-only

# Connect to VPN
uv run python3 gp_saml_selenium.py --gateway vpn.company.com --sudo
```

### Method 2: Direct Python

If dependencies are installed globally:

```bash
# Print credentials only
python3 gp_saml_selenium.py --gateway vpn.company.com --print-only

# Connect to VPN
python3 gp_saml_selenium.py --gateway vpn.company.com --sudo
```

### Method 3: Using the Example Script

```bash
./example.sh vpn.company.com
```

## Common Issues and Solutions

### Issue: ChromeDriver not found

**Error:**
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solution (macOS):**
```bash
brew install chromedriver
xattr -d com.apple.quarantine $(which chromedriver)
```

**Solution (Linux):**
```bash
# Ubuntu/Debian
sudo apt install chromium-chromedriver

# Fedora
sudo dnf install chromium-chromedriver

# Or download manually
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
export LATEST=$(cat LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$LATEST/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

### Issue: OpenConnect not found

**Error:**
```
OpenConnect not found. Please install it
```

**Solution:**
```bash
# macOS
brew install openconnect

# Ubuntu/Debian
sudo apt install openconnect

# Fedora
sudo dnf install openconnect
```

### Issue: Permission denied when running OpenConnect

**Error:**
```
You need to be root to run OpenConnect
```

**Solution:**
Use `--sudo` or `--pkexec` flag:
```bash
uv run python3 gp_saml_selenium.py --gateway vpn.company.com --sudo
```

### Issue: SSL Certificate Verification Failed

**Error:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
Add `--no-verify` flag:
```bash
uv run python3 gp_saml_selenium.py --gateway vpn.company.com --no-verify --sudo
```

### Issue: SAML Credentials Not Extracted

**Symptoms:**
- Browser opens and you complete authentication
- But the script times out saying "Timeout waiting for SAML authentication"

**Solutions:**

1. Try specifying Windows as the client OS (some servers require this):
   ```bash
   uv run python3 gp_saml_selenium.py --gateway vpn.company.com --clientos=Windows --sudo
   ```

2. Increase verbosity to see what's happening:
   ```bash
   uv run python3 gp_saml_selenium.py --gateway vpn.company.com -vv --sudo
   ```

3. Your server might not embed SAML credentials in HTML comments. Check the verbose output to see what's being extracted.

### Issue: Headless Mode Doesn't Work

Headless mode requires either:
- Pre-configured SSO that doesn't need user interaction
- Or it won't work for interactive SAML flows

For interactive SAML, **do not use `--headless`** - you need to see the browser to complete authentication.

## Advanced Configuration

### Using Custom ChromeDriver Path

If ChromeDriver is installed in a non-standard location, set the PATH:

```bash
export PATH="/path/to/chromedriver:$PATH"
uv run python3 gp_saml_selenium.py --gateway vpn.company.com --sudo
```

### Passing Arguments to OpenConnect

Use `--` to separate OpenConnect arguments:

```bash
uv run python3 gp_saml_selenium.py --gateway vpn.company.com --sudo -- \
  --csd-wrapper=/path/to/hip-report.sh \
  --script=/path/to/vpnc-script
```

### Environment Variables

```bash
# Disable SSL verification for requests library
export PYTHONHTTPSVERIFY=0

# Enable Selenium debug logging
export SELENIUM_DEBUG=1
```

## Testing Without Connecting

To test the authentication flow without actually connecting to the VPN:

```bash
uv run python3 gp_saml_selenium.py --gateway vpn.company.com --print-only
```

This will:
1. Query the prelogin endpoint
2. Open the browser for SAML auth
3. Extract credentials
4. Print the OpenConnect command and credentials
5. Exit without connecting

## Troubleshooting Steps

1. **Verify system dependencies:**
   ```bash
   which openconnect  # Should show a path
   which chromedriver # Should show a path
   which google-chrome || which chromium  # Should show a path
   ```

2. **Test ChromeDriver:**
   ```bash
   chromedriver --version
   ```

3. **Test OpenConnect:**
   ```bash
   openconnect --version
   ```

4. **Run validation script:**
   ```bash
   uv run python3 validate.py
   ```

5. **Test with maximum verbosity:**
   ```bash
   uv run python3 gp_saml_selenium.py --gateway vpn.company.com -vvv --print-only
   ```

## Security Considerations

- **Never use `--no-verify` in production** unless you understand the security implications
- The script stores credentials in memory only and passes them via stdin to OpenConnect
- Browser history and cookies are not persisted (Selenium uses a clean profile)
- Consider using `--headless` for automated deployments (if your SAML flow supports it)

## Getting Help

If you encounter issues:

1. Run with verbose logging: `-vv` or `-vvv`
2. Check the troubleshooting section above
3. Verify all system dependencies are installed
4. Test with `--print-only` first before attempting to connect
5. Check if your GlobalProtect server requires specific `--clientos` value
