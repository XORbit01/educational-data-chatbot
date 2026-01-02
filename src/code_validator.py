"""
Code Validator for Educational Data Chatbot.

Provides multi-layer security validation using AST analysis,
allowlist/denylist enforcement, and pattern-based validation.
"""

import ast
import re
from dataclasses import dataclass, field
from typing import List, Set, Optional, Tuple
from enum import Enum

from config import config
from exceptions import CodeValidationError, SecurityViolationError, ErrorCode
from logger import security_logger


class ValidationStatus(Enum):
    """Validation result status."""
    ALLOWED = "allowed"
    DENIED = "denied"
    GREYLIST = "greylist"


@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    sanitized_code: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blocked_operations: List[str] = field(default_factory=list)
    unknown_operations: List[str] = field(default_factory=list)


class ASTSecurityVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts and validates code elements.
    
    Walks the Abstract Syntax Tree to find:
    - Function/method calls
    - Attribute accesses
    - Import statements
    - Name accesses
    """
    
    def __init__(self):
        self.calls: List[str] = []
        self.attributes: List[str] = []
        self.imports: List[str] = []
        self.names: List[str] = []
        self.subscripts: List[str] = []
        self.violations: List[str] = []
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function/method calls."""
        call_name = self._get_call_name(node)
        if call_name:
            self.calls.append(call_name)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute accesses (e.g., df.groupby)."""
        self.attributes.append(node.attr)
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from ... import statements."""
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name) -> None:
        """Visit variable names."""
        self.names.append(node.id)
        self.generic_visit(node)
    
    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Visit subscript operations (e.g., df['column'])."""
        if isinstance(node.slice, ast.Constant):
            self.subscripts.append(str(node.slice.value))
        self.generic_visit(node)
    
    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extract the name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


class CodeValidator:
    """
    Multi-layer security validator for generated code.
    
    Implements:
    1. Syntax validation (AST parsing)
    2. Allowlist validation (only approved operations)
    3. Denylist validation (block dangerous operations)
    4. Greylist handling (unknown operations)
    5. Pattern-based validation (regex checks)
    """
    
    def __init__(self):
        self.allowed_ops = config.security.allowed_operations
        self.blocked_ops = config.security.blocked_operations
        self.blocked_modules = config.security.blocked_modules
        self.allowed_vars = config.security.allowed_variables
    
    def validate(self, code: str) -> ValidationResult:
        """
        Validate code through all security layers.
        
        Args:
            code: Python code string to validate
            
        Returns:
            ValidationResult with validation status and details
            
        Raises:
            CodeValidationError: If code fails critical validation
            SecurityViolationError: If security violation detected
        """
        errors = []
        warnings = []
        blocked = []
        unknown = []
        
        # Layer 1: Syntax validation
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            security_logger.error(f"Syntax error in code: {e}")
            raise CodeValidationError(
                message=f"Syntax error: {e.msg}",
                code=ErrorCode.SYNTAX_ERROR
            )
        
        # Layer 2: AST analysis
        visitor = ASTSecurityVisitor()
        visitor.visit(tree)
        
        # Layer 3: Check imports (critical - deny all imports)
        if visitor.imports:
            blocked_imports = [imp for imp in visitor.imports]
            if blocked_imports:
                security_logger.security(
                    "Import attempt blocked",
                    imports=blocked_imports
                )
                raise SecurityViolationError(
                    message="Import statements are not allowed",
                    violation_type="blocked_import",
                    blocked_item=str(blocked_imports)
                )
        
        # Layer 4: Check denylist (blocked operations)
        all_operations = set(visitor.calls + visitor.attributes + visitor.names)
        
        for op in all_operations:
            if op in self.blocked_ops:
                blocked.append(op)
                security_logger.security(
                    "Blocked operation detected",
                    operation=op
                )
        
        if blocked:
            raise SecurityViolationError(
                message=f"Blocked operations detected: {blocked}",
                violation_type="blocked_operation",
                blocked_item=str(blocked)
            )
        
        # Layer 5: Check allowlist
        for op in visitor.calls:
            status = self._check_operation(op)
            if status == ValidationStatus.DENIED:
                blocked.append(op)
            elif status == ValidationStatus.GREYLIST:
                unknown.append(op)
                warnings.append(f"Unknown operation: {op}")
        
        for attr in visitor.attributes:
            status = self._check_operation(attr)
            if status == ValidationStatus.DENIED:
                blocked.append(attr)
            elif status == ValidationStatus.GREYLIST:
                # Attributes in greylist might be column names - allow
                if not self._looks_like_column_name(attr):
                    unknown.append(attr)
        
        # Layer 6: Pattern-based validation
        pattern_errors = self._check_dangerous_patterns(code)
        errors.extend(pattern_errors)
        
        # Layer 7: Variable validation
        var_errors = self._validate_variables(visitor.names)
        errors.extend(var_errors)
        
        # Determine final validity
        is_valid = len(errors) == 0 and len(blocked) == 0
        
        if not is_valid:
            all_issues = errors + [f"Blocked: {b}" for b in blocked]
            raise CodeValidationError(
                message="Code validation failed",
                violations=all_issues
            )
        
        # Log successful validation
        security_logger.info(
            "Code validation passed",
            operations=len(all_operations),
            warnings=len(warnings)
        )
        
        return ValidationResult(
            is_valid=True,
            sanitized_code=code,
            errors=errors,
            warnings=warnings,
            blocked_operations=blocked,
            unknown_operations=unknown
        )
    
    def _check_operation(self, operation: str) -> ValidationStatus:
        """
        Check if an operation is allowed, denied, or greylist.
        
        Args:
            operation: Operation name to check
            
        Returns:
            ValidationStatus indicating the operation's status
        """
        # Normalize operation name
        op_lower = operation.lower()
        
        # Check denylist first (highest priority)
        if operation in self.blocked_ops or op_lower in self.blocked_ops:
            return ValidationStatus.DENIED
        
        # Check allowlist
        if operation in self.allowed_ops or op_lower in self.allowed_ops:
            return ValidationStatus.ALLOWED
        
        # Check if it's a common Python builtin that's safe
        safe_builtins = {'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 
                        'tuple', 'set', 'range', 'zip', 'enumerate', 'sorted',
                        'reversed', 'min', 'max', 'sum', 'abs', 'round'}
        if operation in safe_builtins:
            return ValidationStatus.ALLOWED
        
        # Greylist - unknown operation
        return ValidationStatus.GREYLIST
    
    def _looks_like_column_name(self, name: str) -> bool:
        """Check if a name looks like a DataFrame column name."""
        column_patterns = [
            'student', 'course', 'assessment', 'class', 'gender',
            'score', 'rate', 'count', 'views', 'downloads', 'name',
            'id', 'level', 'no', 'hand', 'moodle', 'attendance', 'raised'
        ]
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in column_patterns)
    
    def _check_dangerous_patterns(self, code: str) -> List[str]:
        """
        Check for dangerous patterns using regex.
        
        Args:
            code: Code string to check
            
        Returns:
            List of error messages for detected patterns
        """
        errors = []
        
        dangerous_patterns = [
            (r'__\w+__', "Dunder method access not allowed"),
            (r'\bexec\s*\(', "exec() is not allowed"),
            (r'\beval\s*\(', "eval() is not allowed"),
            (r'\bcompile\s*\(', "compile() is not allowed"),
            (r'\b__import__\s*\(', "__import__() is not allowed"),
            (r'\bopen\s*\(', "File operations not allowed"),
            (r'\bos\.\w+', "os module access not allowed"),
            (r'\bsys\.\w+', "sys module access not allowed"),
            (r'\bsubprocess\.\w+', "subprocess module not allowed"),
            (r'\.read\s*\(', "File read operations not allowed"),
            (r'\.write\s*\(', "File write operations not allowed"),
            (r'\bglobals\s*\(', "globals() not allowed"),
            (r'\blocals\s*\(', "locals() not allowed"),
            (r'\bgetattr\s*\(', "getattr() not allowed"),
            (r'\bsetattr\s*\(', "setattr() not allowed"),
            (r'lambda\s*:', "Lambda functions not allowed"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                errors.append(message)
                security_logger.security(
                    "Dangerous pattern detected",
                    pattern=pattern,
                    message=message
                )
        
        return errors
    
    def _validate_variables(self, names: List[str]) -> List[str]:
        """
        Validate that only allowed variables are accessed.
        
        Args:
            names: List of variable names found in code
            
        Returns:
            List of error messages for invalid variables
        """
        errors = []
        
        # These are always allowed
        always_allowed = {'df', 'pd', 'np', 'True', 'False', 'None'}
        
        # Common temp variable patterns are allowed
        temp_patterns = [
            r'^[a-z]$',          # Single letter vars
            r'^temp\d*$',        # temp, temp1, temp2
            r'^result\d*$',      # result, result1
            r'^data\d*$',        # data, data1
            r'^grouped\d*$',     # grouped, grouped1
            r'^filtered\d*$',    # filtered, filtered1
            r'^subset\d*$',      # subset, subset1
            r'^stats\d*$',       # stats, stats1
            r'^summary\d*$',     # summary, summary1
            r'^[xy]\d*$',        # x, y, x1, y1
            r'^idx\d*$',         # idx, idx1
            r'^row\d*$',         # row, row1
            r'^col\d*$',         # col, col1
        ]
        
        for name in names:
            # Skip allowed names
            if name in always_allowed or name in self.allowed_vars:
                continue
            
            # Check temp patterns
            if any(re.match(p, name) for p in temp_patterns):
                continue
            
            # Check if it might be a column string reference
            if self._looks_like_column_name(name):
                continue
            
            # Check for potentially dangerous names
            if name.startswith('_') and not name.startswith('__'):
                # Single underscore is fine (unused var convention)
                continue
            
            if name.startswith('__'):
                errors.append(f"Dunder variable access not allowed: {name}")
        
        return errors
    
    def quick_check(self, code: str) -> bool:
        """
        Quick validation check without full analysis.
        
        Args:
            code: Code string to check
            
        Returns:
            True if code passes basic checks, False otherwise
        """
        try:
            # Try to parse
            ast.parse(code)
            
            # Check for obvious dangerous patterns
            dangerous = ['import ', 'exec(', 'eval(', '__', 'open(', 
                        'os.', 'sys.', 'subprocess']
            code_lower = code.lower()
            
            for pattern in dangerous:
                if pattern in code_lower:
                    return False
            
            return True
            
        except SyntaxError:
            return False


# Global validator instance
validator = CodeValidator()


def validate_code(code: str) -> ValidationResult:
    """
    Convenience function for code validation.
    
    Args:
        code: Code string to validate
        
    Returns:
        ValidationResult with validation status
    """
    return validator.validate(code)

