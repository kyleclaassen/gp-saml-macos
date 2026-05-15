#!/usr/bin/env python3
"""
GlobalProtect SAML Authentication using Selenium
Performs SAML authentication and automatically connects to GlobalProtect VPN using OpenConnect.
Works on macOS and Linux.
"""

import argparse
import sys
import time
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from base64 import b64decode
from urllib.parse import urlparse, urlencode
from html.parser import HTMLParser

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class CommentHtmlParser(HTMLParser):
    """Parse HTML comments to extract SAML data."""
    def __init__(self):
        super().__init__()
        self.comments = []

    def handle_comment(self, data: str) -> None:
        self.comments.append(data)


class GPSAMLAuthenticator:
    """GlobalProtect SAML Authenticator using Selenium."""
    
    COOKIE_FIELDS = ('prelogin-cookie', 'portal-userauthcookie')
    USER_AGENT = 'PAN GlobalProtect'
    
    def __init__(self, args):
        self.args = args
        self.server = args.server
        self.interface = args.interface
        self.verbose = args.verbose
        self.verify = args.verify
        self.saml_result = {}
        self.driver = None
        
    def log(self, message, level=1):
        """Print log message if verbosity level is sufficient."""
        if self.verbose >= level:
            print(f"[INFO] {message}", file=sys.stderr)
    
    def error(self, message):
        """Print error message and exit."""
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)
    
    def get_prelogin_info(self):
        """Query GlobalProtect prelogin endpoint to get SAML configuration."""
        if2prelogin = {
            'portal': 'global-protect/prelogin.esp',
            'gateway': 'ssl-vpn/prelogin.esp'
        }
        
        endpoint = f'https://{self.server}/{if2prelogin[self.interface]}'
        data = {
            'tmp': 'tmp',
            'kerberos-support': 'yes',
            'ipv6-support': 'yes',
            'clientVer': 4100,
            'clientos': self.args.clientos,
        }
        
        self.log(f"Querying prelogin endpoint: {endpoint}")
        
        session = requests.Session()
        session.headers['User-Agent'] = self.USER_AGENT
        
        try:
            response = session.post(endpoint, verify=self.verify, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.error(f"Failed to connect to {endpoint}: {e}")
        
        try:
            xml = ET.fromstring(response.content)
        except ET.ParseError:
            self.log(f"HTTP {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}")
            self.log(f"Response preview: {response.content[:300]}", level=2)
            self.error(
                f"Invalid XML response from prelogin endpoint "
                f"(HTTP {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}). "
                f"Server may have returned an HTML page instead of XML — check --no-verify if SSL is the issue."
            )
        
        if xml.tag != 'prelogin-response':
            self.error(f"Unexpected response tag: {xml.tag}")
        
        status = xml.find('status')
        if status is not None and status.text != 'Success':
            msg = xml.find('msg')
            error_msg = msg.text if msg is not None else 'Unknown error'
            if error_msg == f'GlobalProtect {self.interface} does not exist':
                other = 'portal' if self.interface == 'gateway' else 'gateway'
                self.error(f"{self.interface.title()} interface does not exist. Try --{other} instead.")
            else:
                self.error(f"Prelogin failed: {error_msg}")
        
        saml_method = xml.find('saml-auth-method')
        saml_request = xml.find('saml-request')
        
        if saml_method is None or saml_request is None:
            self.error(
                f"No SAML authentication required. This tool only supports SAML auth.\n"
                f"Try different --clientos value (e.g., --clientos=Windows) or use standard authentication."
            )
        
        method = saml_method.text
        request_data = b64decode(saml_request.text).decode('utf-8')
        
        self.log(f"SAML method: {method}")
        
        return method, request_data
    
    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome."""
        chrome_options = Options()
        
        # Headless mode if requested
        if self.args.headless:
            chrome_options.add_argument('--headless=new')
        
        # Common options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1024,768')
        chrome_options.add_argument(f'user-agent={self.USER_AGENT}')
        
        # Disable certificate verification if requested
        if not self.verify:
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
        
        # Try to find ChromeDriver automatically
        try:
            self.log("Initializing Chrome WebDriver...")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
        except WebDriverException as e:
            self.error(
                f"Failed to initialize Chrome WebDriver: {e}\n"
                f"Please install ChromeDriver: https://chromedriver.chromium.org/\n"
                f"macOS: brew install chromedriver\n"
                f"Linux: sudo apt install chromium-chromedriver or download manually"
            )
    
    def perform_saml_auth(self, method, request_data):
        """Perform SAML authentication using Selenium."""
        self.setup_driver()
        
        try:
            if method == 'REDIRECT':
                # Navigate to SAML redirect URL
                self.log(f"Navigating to SAML redirect URL...")
                self.driver.get(request_data)
            elif method == 'POST':
                # Load HTML form and submit
                self.log(f"Loading SAML POST form...")
                # Write HTML to a temp file and load it
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(request_data)
                    temp_file = f.name
                self.driver.get(f'file://{temp_file}')
            else:
                self.error(f"Unknown SAML method: {method}")
            
            self.log("Waiting for SAML authentication to complete...")
            self.log("Please complete the authentication in the browser window.")
            
            # Wait for SAML response - poll for success indicators
            max_wait = self.args.timeout
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                # Check if we got SAML credentials
                if self.extract_saml_credentials():
                    self.log("Successfully extracted SAML credentials!")
                    return True
                
                # Check if window was closed
                try:
                    _ = self.driver.current_url
                except WebDriverException:
                    self.error("Browser window was closed by user")
                
                time.sleep(0.5)
            
            self.error(f"Timeout waiting for SAML authentication (waited {max_wait}s)")
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def extract_saml_credentials(self):
        """Extract SAML credentials from current page."""
        try:
            current_url = self.driver.current_url
            
            # Get page source
            page_source = self.driver.page_source
            
            # Try to extract from HTML comments (works with most GP servers)
            credentials = self.parse_html_comments(page_source)
            
            if credentials:
                credentials['server'] = urlparse(current_url).netloc
                self.saml_result.update(credentials)
            
            # Check if we have required fields
            has_username = 'saml-username' in self.saml_result
            has_cookie = any(c in self.saml_result for c in self.COOKIE_FIELDS)
            
            if has_username and has_cookie:
                return True
            
            return False
            
        except WebDriverException:
            return False
    
    def parse_html_comments(self, html):
        """Parse SAML data from HTML comments."""
        parser = CommentHtmlParser()
        parser.feed(html)
        
        credentials = {}
        
        for comment in parser.comments:
            # Try to parse as XML
            try:
                # Wrap in fake root to handle multiple tags
                xml_root = ET.fromstring(f"<root>{comment}</root>")
                for elem in xml_root:
                    if elem.tag.startswith('saml-') or elem.tag in self.COOKIE_FIELDS:
                        credentials[elem.tag] = elem.text
                        self.log(f"Found {elem.tag} in HTML comment", level=2)
            except ET.ParseError:
                self.log(f"Comment XML parse failed (special chars?), trying regex fallback", level=2)
            
            # Also try regex pattern matching for robustness
            for match in re.finditer(
                r'<(?P<tag>saml-.+?|(?:prelogin-|portal-userauth)cookie)>(?P<value>.*?)</(?P=tag)>',
                comment
            ):
                tag = match.group('tag')
                value = match.group('value')
                if tag not in credentials:
                    credentials[tag] = value
                    self.log(f"Found {tag} via regex", level=2)
        
        return credentials
    
    def build_openconnect_command(self):
        """Build OpenConnect command from SAML credentials."""
        username = self.saml_result.get('saml-username')
        server = self.saml_result.get('server', self.server)
        
        # Determine which cookie we have
        cookie = None
        cookie_name = None
        for cn in self.COOKIE_FIELDS:
            if cn in self.saml_result:
                cookie = self.saml_result[cn]
                cookie_name = cn
                break
        
        if not username or not cookie:
            self.error("Missing required SAML credentials")
        
        # Map clientos to OpenConnect OS values
        clientos_map = {
            'Linux': 'linux-64',
            'Mac': 'mac-intel',
            'Windows': 'win'
        }
        os_value = clientos_map.get(self.args.clientos, 'linux-64')
        
        usergroup = f"{self.interface}:{cookie_name}"
        
        cmd = [
            'openconnect',
            '--protocol=gp',
            f'--user={username}',
            f'--os={os_value}',
            f'--usergroup={usergroup}',
            '--passwd-on-stdin',
        ]
        
        # Add optional arguments
        if not self.verify:
            cmd.append('--allow-insecure-crypto')
        
        if self.args.no_proxy:
            cmd.append('--no-proxy')
        
        # Use system vpnc-script if available (handles macOS DNS via scutil properly).
        # --script-tun is intentionally NOT used: that flag tells openconnect to
        # pipe raw traffic through the script instead of calling it with
        # reason=connect/disconnect, which breaks standard vpnc-scripts entirely.
        import os
        system_vpnc_paths = [
            '/opt/homebrew/etc/vpnc/vpnc-script',  # Apple Silicon
            '/usr/local/etc/vpnc/vpnc-script',     # Intel Mac
        ]
        local_vpnc = os.path.join(os.path.dirname(__file__), 'vpnc-script-macos.sh')
        chosen_script = next(
            (p for p in system_vpnc_paths if os.path.exists(p)),
            local_vpnc if os.path.exists(local_vpnc) else None,
        )
        if chosen_script:
            cmd.extend(['--script', chosen_script])
            if self.verbose:
                self.log(f"Using vpnc-script: {chosen_script}")
        
        # Add extra OpenConnect arguments
        if self.args.openconnect_args:
            cmd.extend(self.args.openconnect_args)
        
        # Add server
        cmd.append(server)
        
        return cmd, cookie
    
    def connect_vpn(self):
        """Connect to VPN using OpenConnect."""
        cmd, cookie = self.build_openconnect_command()
        
        self.log("\nOpenConnect command:")
        cmd_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in cmd)
        self.log(f"  echo '<cookie>' | {cmd_str}")
        
        if self.args.print_only:
            # Print credentials for manual use
            print("\n# Export these variables:")
            print(f"HOST=https://{self.saml_result.get('server', self.server)}/{self.interface}:{cmd[4].split('=')[1].split(':')[1]}")
            print(f"USER={self.saml_result.get('saml-username')}")
            print(f"COOKIE={cookie}")
            print(f"OS={cmd[3].split('=')[1]}")
            print("\n# Or run OpenConnect directly:")
            print(f"echo '{cookie}' | {cmd_str}")
            return
        
        # Execute OpenConnect
        self.log("\nConnecting to VPN...")
        
        # Determine privilege escalation method
        if self.args.sudo:
            cmd.insert(0, 'sudo')
        elif self.args.pkexec:
            cmd = ['pkexec'] + cmd
        
        try:
            # Pass cookie via stdin
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Send cookie and close stdin
            process.stdin.write(cookie + '\n')
            process.stdin.close()
            
            # Stream output
            for line in process.stdout:
                print(line, end='')
            
            process.wait()
            
            if process.returncode != 0:
                self.error(f"OpenConnect exited with code {process.returncode}")
                
        except FileNotFoundError:
            self.error(
                "OpenConnect not found. Please install it:\n"
                "  macOS: brew install openconnect\n"
                "  Ubuntu/Debian: sudo apt install openconnect\n"
                "  Fedora: sudo dnf install openconnect"
            )
        except KeyboardInterrupt:
            self.log("\nDisconnecting...")
            process.terminate()
            sys.exit(0)
    
    def run(self):
        """Main execution flow."""
        self.log(f"Authenticating to GlobalProtect {self.interface}: {self.server}")
        
        # Step 1: Get SAML configuration
        method, request_data = self.get_prelogin_info()
        
        # Step 2: Perform SAML authentication
        self.perform_saml_auth(method, request_data)
        
        # Step 3: Connect VPN
        self.connect_vpn()


def main():
    parser = argparse.ArgumentParser(
        description='GlobalProtect SAML Authentication using Selenium',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Authenticate and print credentials
  %(prog)s --gateway vpn.company.com --print-only
  
  # Authenticate and connect with sudo
  %(prog)s --gateway vpn.company.com --sudo
  
  # Portal authentication (headless mode)
  %(prog)s --portal vpn.company.com --headless --sudo
  
  # With extra OpenConnect arguments
  %(prog)s --gateway vpn.company.com --sudo -- --csd-wrapper=hip-report.sh
        """
    )
    
    # Required arguments
    parser.add_argument('server', help='GlobalProtect server (portal or gateway)')
    
    # Interface selection
    interface_group = parser.add_mutually_exclusive_group()
    interface_group.add_argument(
        '-g', '--gateway',
        dest='interface',
        action='store_const',
        const='gateway',
        help='Authenticate to gateway (use with gateway URL)'
    )
    interface_group.add_argument(
        '-p', '--portal',
        dest='interface',
        action='store_const',
        const='portal',
        default='portal',
        help='Authenticate to portal (default)'
    )
    
    # Browser options
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no GUI)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        metavar='SECONDS',
        help='Authentication timeout in seconds (default: 300)'
    )
    
    # Connection options
    parser.add_argument(
        '--clientos',
        choices=['Linux', 'Mac', 'Windows'],
        default='Windows',
        help='OS identifier to send to server (default: Windows)'
    )
    parser.add_argument(
        '--no-verify',
        dest='verify',
        action='store_false',
        default=True,
        help='Ignore invalid SSL certificates'
    )
    parser.add_argument(
        '--no-proxy',
        action='store_true',
        help='Disable system proxy for VPN connection'
    )
    
    # Execution mode
    exec_group = parser.add_mutually_exclusive_group()
    exec_group.add_argument(
        '--print-only',
        action='store_true',
        help='Print credentials without connecting'
    )
    exec_group.add_argument(
        '--sudo',
        action='store_true',
        help='Run OpenConnect with sudo'
    )
    exec_group.add_argument(
        '--pkexec',
        action='store_true',
        help='Run OpenConnect with pkexec (PolicyKit)'
    )
    
    # Verbosity
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=1,
        help='Increase verbosity (can be used multiple times)'
    )
    parser.add_argument(
        '-q', '--quiet',
        dest='verbose',
        action='store_const',
        const=0,
        help='Suppress informational output'
    )
    
    # Extra OpenConnect arguments
    parser.add_argument(
        'openconnect_args',
        nargs='*',
        help='Additional arguments to pass to OpenConnect'
    )
    
    args = parser.parse_args()
    
    # Validate
    if not args.print_only and not args.sudo and not args.pkexec:
        parser.error(
            "Must specify execution mode: --print-only, --sudo, or --pkexec\n"
            "OpenConnect requires root privileges to create VPN tunnel."
        )
    
    # Run authenticator
    authenticator = GPSAMLAuthenticator(args)
    authenticator.run()


if __name__ == '__main__':
    main()
