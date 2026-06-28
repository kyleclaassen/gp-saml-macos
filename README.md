# GlobalProtect SAML Authenticator (Selenium)

Cross-platform Python tool for authenticating to GlobalProtect VPN servers that use SAML (Single Sign-On).

## Features

- ✅ **Cross-platform**: Works on macOS and Linux
- ✅ **Selenium-based**: Uses Firefox for reliable browser automation
- ✅ **Headless mode**: Can run without GUI for automation
- ✅ **Auto-connect**: Automatically calls OpenConnect after authentication
- ✅ **Flexible**: Supports both portal and gateway authentication

## Requirements

### System Dependencies

**macOS:**
```bash
brew install openconnect
brew install geckodriver
```

**Ubuntu/Debian:**
```bash
sudo apt install openconnect firefox-geckodriver
```

**Fedora:**
```bash
sudo dnf install openconnect firefox-geckodriver
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install requests selenium
```

## Usage

### Basic Authentication (Print Credentials)

```bash
# Gateway authentication
python3 gp_saml_selenium.py --gateway vpn.company.com --print-only

# Portal authentication
python3 gp_saml_selenium.py --portal vpn.company.com --print-only
```

### Connect to VPN

```bash
# Using sudo (recommended)
python3 gp_saml_selenium.py --gateway vpn.company.com --sudo

# Using pkexec (PolicyKit)
python3 gp_saml_selenium.py --gateway vpn.company.com --pkexec
```

### Headless Mode

Run without showing the browser window (requires completing auth via other means or with pre-configured SSO):

```bash
python3 gp_saml_selenium.py --gateway vpn.company.com --headless --sudo
```

### Advanced Options

```bash
# Ignore SSL certificate errors
python3 gp_saml_selenium.py --gateway vpn.company.com --no-verify --sudo

# Specify client OS type (some servers require Windows)
python3 gp_saml_selenium.py --gateway vpn.company.com --clientos=Windows --sudo

# Pass extra arguments to OpenConnect
python3 gp_saml_selenium.py --gateway vpn.company.com --sudo -- --csd-wrapper=hip-report.sh

# Increase verbosity
python3 gp_saml_selenium.py --gateway vpn.company.com -vv --sudo
```

## How It Works

1. **Prelogin Query**: Contacts the GlobalProtect server to discover SAML configuration
2. **Browser Launch**: Opens Firefox with Selenium to handle SAML authentication
3. **User Authentication**: You complete the SSO login (Okta, Microsoft, etc.) in the browser
4. **Credential Extraction**: Extracts SAML cookies from HTML comments in the response
5. **VPN Connection**: Automatically calls OpenConnect with the authentication cookie

## Architecture

```
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│     CLI      │─────▶│  gp_saml_selenium│─────▶│ GlobalProtect│
│              │      │                  │      │   Server     │
└──────────────┘      └──────────────────┘      └──────────────┘
                              │                         │
                              ▼                         ▼
                      ┌──────────────┐          ┌──────────────┐
                      │   Selenium   │          │ SAML Identity│
                      │   Firefox    │◀────────▶│   Provider   │
                      │  WebDriver   │          │ (Okta, etc.) │
                      └──────────────┘          └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │  OpenConnect │
                      │     VPN      │
                      └──────────────┘
```

## Troubleshooting

### Driver not found

**macOS:**
```bash
brew install geckodriver
# If security warning appears:
xattr -d com.apple.quarantine $(which geckodriver)
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install firefox-geckodriver

# Or download manually from:
# https://github.com/mozilla/geckodriver/
```

### OpenConnect not found

Install OpenConnect for your platform:

**macOS:**
```bash
brew install openconnect
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install openconnect

# Fedora
sudo dnf install openconnect
```

### SSL Certificate Errors

If the server uses self-signed certificates:
```bash
python3 gp_saml_selenium.py --gateway vpn.company.com --no-verify --sudo
```

### SAML Credentials Not Extracted

Some GlobalProtect servers may not embed SAML data in HTML comments. This tool requires servers that follow this pattern (most do). If your server doesn't work, try:

1. Check if the server requires a specific `--clientos` value:
   ```bash
   python3 gp_saml_selenium.py --gateway vpn.company.com --clientos=Windows --sudo
   ```

2. Increase verbosity to see what's happening:
   ```bash
   python3 gp_saml_selenium.py --gateway vpn.company.com -vv --sudo
   ```

## Differences from gp-saml-gui

| Feature | gp-saml-gui | gp_saml_selenium.py |
|---------|-------------|---------------------|
| Browser Engine | WebKit2-GTK / pywebview | Selenium + Firefox |
| macOS Support | Limited (requires pywebview) | Native |
| Linux Support | Yes (WebKit2-GTK) | Yes |
| Headless Mode | No | Yes |
| Dependencies | GTK3, WebKit2 | Firefox |
| Installation | Complex on macOS | Simple (pip + brew/apt) |

## License

GPLv3 or newer (compatible with gp-saml-gui)

## Credits

Based on research of:
- [dlenski/gp-saml-gui](https://github.com/dlenski/gp-saml-gui) - Original SAML authentication tool
- [lkrms/gp-saml-gui](https://github.com/lkrms/gp-saml-gui) - macOS-compatible fork
- [dlenski/openconnect](https://github.com/dlenski/openconnect) - GlobalProtect protocol documentation
