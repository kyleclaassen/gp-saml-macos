#!/usr/bin/env python3
"""Basic functionality tests for gp_saml_selenium.py"""

import sys

def test_imports():
    """Test that all required modules can be imported."""
    try:
        import requests
        import selenium
        from selenium import webdriver
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_module_structure():
    """Test that the main module has expected structure."""
    try:
        import gp_saml_selenium
        
        # Check for main classes
        assert hasattr(gp_saml_selenium, 'CommentHtmlParser')
        assert hasattr(gp_saml_selenium, 'GPSAMLAuthenticator')
        assert hasattr(gp_saml_selenium, 'main')
        
        print("✓ Module structure valid")
        return True
    except (ImportError, AssertionError) as e:
        print(f"✗ Module structure test failed: {e}")
        return False

def test_argument_parser():
    """Test that argument parser works."""
    try:
        import gp_saml_selenium
        import argparse
        
        # This will fail because we don't provide required args, but that's expected
        try:
            gp_saml_selenium.main()
        except SystemExit as e:
            # Expected to exit with error due to missing args
            if e.code == 2:  # argparse error code
                print("✓ Argument parser works")
                return True
        
        return False
    except Exception as e:
        print(f"✗ Argument parser test failed: {e}")
        return False

if __name__ == '__main__':
    print("Running basic tests...\n")
    
    results = [
        test_imports(),
        test_module_structure(),
        test_argument_parser(),
    ]
    
    print(f"\nResults: {sum(results)}/{len(results)} tests passed")
    sys.exit(0 if all(results) else 1)
