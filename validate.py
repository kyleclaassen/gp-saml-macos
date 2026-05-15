#!/usr/bin/env python3
"""
Quick validation script to check if gp_saml_selenium.py is syntactically correct
and has all required components.
"""

import ast
import sys

def validate_script(filename):
    """Validate Python script syntax and structure."""
    print(f"Validating {filename}...")
    
    try:
        with open(filename, 'r') as f:
            source = f.read()
        
        # Parse AST
        tree = ast.parse(source, filename=filename)
        
        # Find classes
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        print(f"✓ Found {len(classes)} classes: {', '.join(classes)}")
        
        # Find functions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        print(f"✓ Found {len(functions)} functions")
        
        # Check for required imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        required = ['requests', 'selenium', 'argparse', 'subprocess']
        missing = [req for req in required if not any(req in imp for imp in imports)]
        
        if missing:
            print(f"✗ Missing imports: {', '.join(missing)}")
            return False
        
        print(f"✓ All required imports present")
        print(f"✓ Syntax is valid!")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    success = validate_script('gp_saml_selenium.py')
    sys.exit(0 if success else 1)
