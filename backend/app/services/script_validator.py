"""
Script Validator Service
Validates uploaded Python scripts for security and correctness
"""

import ast
from typing import Dict, List


class ScriptValidator:
    """Validates extension scripts for security and functionality"""
    
    # Forbidden imports that could be security risks
    FORBIDDEN_IMPORTS = [
        'os', 'subprocess', 'sys', 'shutil', 'socket',
        '__import__', 'eval', 'exec', 'compile', 'execfile',
        'importlib', 'ctypes', 'multiprocessing'
    ]
    
    # Forbidden function calls
    FORBIDDEN_CALLS = [
        'open', 'compile', 'eval', 'exec', '__import__',
        'delattr', 'setattr', 'vars', 'dir'
    ]
    
    # Allowed safe imports
    ALLOWED_IMPORTS = [
        'json', 'csv', 'datetime', 'math', 'statistics',
        'collections', 'itertools', 'functools', 're',
        'typing', 'dataclasses', 'enum',
        # Data science (if needed)
        'numpy', 'pandas', 'matplotlib', 'seaborn'
    ]
    
    @staticmethod
    def validate(script_content: bytes, handler_function: str) -> Dict[str, any]:
        """
        Validate Python script for security and structure
        
        Args:
            script_content: Script file content as bytes
            handler_function: Name of the handler function to execute
            
        Returns:
            dict with 'valid' (bool) and 'error' (str) or 'warnings' (list)
        """
        try:
            script_str = script_content.decode('utf-8')
            
            # Check size limit (max 1MB)
            if len(script_content) > 1024 * 1024:
                return {
                    "valid": False,
                    "error": "Script file too large (max 1MB)"
                }
            
            # Parse Python AST (Abstract Syntax Tree)
            try:
                tree = ast.parse(script_str)
            except SyntaxError as e:
                return {
                    "valid": False,
                    "error": f"Syntax error at line {e.lineno}: {e.msg}"
                }
            
            # Security checks
            security_check = ScriptValidator._check_security(tree)
            if not security_check["valid"]:
                return security_check
            
            # Check handler function exists
            function_check = ScriptValidator._check_handler_function(tree, handler_function)
            if not function_check["valid"]:
                return function_check
            
            # Extract warnings (non-fatal issues)
            warnings = ScriptValidator._extract_warnings(tree)
            
            return {
                "valid": True,
                "warnings": warnings,
                "message": "Script validation passed"
            }
        
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }
    
    @staticmethod
    def _check_security(tree: ast.AST) -> Dict[str, any]:
        """Check for security violations in the AST"""
        
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]  # Get top-level module
                    if module_name in ScriptValidator.FORBIDDEN_IMPORTS:
                        return {
                            "valid": False,
                            "error": f"Forbidden import: '{alias.name}' (security risk)"
                        }
            
            # Check from...import statements
            if isinstance(node, ast.ImportFrom):
                module_name = node.module.split('.')[0] if node.module else ''
                if module_name in ScriptValidator.FORBIDDEN_IMPORTS:
                    return {
                        "valid": False,
                        "error": f"Forbidden import: 'from {node.module}' (security risk)"
                    }
            
            # Check function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ScriptValidator.FORBIDDEN_CALLS:
                        return {
                            "valid": False,
                            "error": f"Forbidden function call: '{node.func.id}()' (security risk)"
                        }
        
        return {"valid": True}
    
    @staticmethod
    def _check_handler_function(tree: ast.AST, handler_function: str) -> Dict[str, any]:
        """Verify handler function exists with correct signature"""
        
        function_found = False
        function_params = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == handler_function:
                function_found = True
                function_params = [arg.arg for arg in node.args.args]
                break
        
        if not function_found:
            return {
                "valid": False,
                "error": f"Handler function '{handler_function}' not found in script"
            }
        
        # Check required parameters
        required_params = ['file_data']
        for param in required_params:
            if param not in function_params:
                return {
                    "valid": False,
                    "error": f"Handler function must have '{param}' parameter"
                }
        
        return {"valid": True, "params": function_params}
    
    @staticmethod
    def _extract_warnings(tree: ast.AST) -> List[str]:
        """Extract non-fatal warnings from the script"""
        warnings = []
        
        # Check for print statements (not necessarily bad, but worth noting)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    warnings.append("Script contains print() statements (may affect output)")
        
        return warnings
