"""
Custom Exceptions for Educational Data Chatbot.

Provides typed exceptions for different error scenarios
with helpful messages and error codes.

Developer: aliawada127001@outlook.com
"""

from enum import Enum
from typing import Optional, List


class ErrorCode(Enum):
    """Error codes for categorizing exceptions."""
    # Code Generation Errors (1xx)
    LLM_CONNECTION_ERROR = 101
    LLM_TIMEOUT = 102
    LLM_INVALID_RESPONSE = 103
    CODE_EXTRACTION_FAILED = 104
    
    # Validation Errors (2xx)
    VALIDATION_FAILED = 201
    BLOCKED_OPERATION = 202
    BLOCKED_MODULE = 203
    SYNTAX_ERROR = 204
    UNKNOWN_OPERATION = 205
    
    # Execution Errors (3xx)
    EXECUTION_FAILED = 301
    EXECUTION_TIMEOUT = 302
    MEMORY_LIMIT = 303
    RUNTIME_ERROR = 304
    
    # Security Errors (4xx)
    SECURITY_VIOLATION = 401
    INPUT_TOO_LONG = 402
    INJECTION_ATTEMPT = 403
    
    # Data Errors (5xx)
    DATA_LOAD_ERROR = 501
    INVALID_COLUMN = 502
    DATA_TYPE_ERROR = 503


class ChatbotError(Exception):
    """Base exception for all chatbot errors."""
    
    def __init__(
        self, 
        message: str, 
        code: ErrorCode,
        details: Optional[str] = None,
        user_message: Optional[str] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        # User-friendly message (safe to display)
        self.user_message = user_message or message
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"[{self.code.name}] {self.message}"


class CodeGenerationError(ChatbotError):
    """Raised when LLM fails to generate valid code."""
    
    def __init__(
        self, 
        message: str,
        code: ErrorCode = ErrorCode.LLM_INVALID_RESPONSE,
        details: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
            user_message="I couldn't generate the code for your question. Please try rephrasing."
        )


class CodeValidationError(ChatbotError):
    """Raised when generated code fails security validation."""
    
    def __init__(
        self, 
        message: str,
        violations: Optional[List[str]] = None,
        code: ErrorCode = ErrorCode.VALIDATION_FAILED
    ):
        self.violations = violations or []
        
        # Provide specific user messages based on error type
        if code == ErrorCode.SYNTAX_ERROR:
            user_msg = f"Syntax error in generated code: {message}. The AI generated invalid code. Please try rephrasing your question."
        elif violations:
            user_msg = f"Security validation failed: {', '.join(violations[:2])}. Please try a different question."
        else:
            user_msg = "The generated code contains unsafe operations. Please try a different question."
        
        super().__init__(
            message=message,
            code=code,
            details=", ".join(self.violations) if self.violations else None,
            user_message=user_msg
        )


class SecurityViolationError(ChatbotError):
    """Raised when a security violation is detected."""
    
    def __init__(
        self, 
        message: str,
        violation_type: str,
        blocked_item: str,
        code: ErrorCode = ErrorCode.SECURITY_VIOLATION
    ):
        self.violation_type = violation_type
        self.blocked_item = blocked_item
        # More informative error message for debugging
        if "lambda" in blocked_item.lower():
            user_msg = "Lambda functions are not supported. Please try a different query."
        elif "import" in violation_type.lower():
            # Show what import was attempted
            # blocked_item is a string representation of a list like "['plotly', 'pandas']"
            imports_str = blocked_item
            if blocked_item.startswith('[') and blocked_item.endswith(']'):
                # Parse the list string safely
                imports_str = blocked_item.strip('[]').replace("'", "").replace('"', '')
            user_msg = f"Import statements are not allowed (attempted: {imports_str}). All libraries (px, go, pd, np, df) are already imported. Please rephrase your question."
        else:
            user_msg = f"Security block: {blocked_item}. Please try rephrasing your question."
        super().__init__(
            message=message,
            code=code,
            details=f"{violation_type}: {blocked_item}",
            user_message=user_msg
        )


class CodeExecutionError(ChatbotError):
    """Raised when code execution fails."""
    
    def __init__(
        self, 
        message: str,
        original_error: Optional[str] = None,
        code: ErrorCode = ErrorCode.EXECUTION_FAILED
    ):
        self.original_error = original_error
        super().__init__(
            message=message,
            code=code,
            details=original_error,
            user_message="There was an error executing the analysis. Please try a different question."
        )


class ExecutionTimeoutError(CodeExecutionError):
    """Raised when code execution times out."""
    
    def __init__(self, timeout_seconds: int):
        super().__init__(
            message=f"Code execution timed out after {timeout_seconds} seconds",
            code=ErrorCode.EXECUTION_TIMEOUT
        )
        self.user_message = "The query took too long. Please try a simpler question."


class DataLoadError(ChatbotError):
    """Raised when data file cannot be loaded."""
    
    def __init__(self, message: str, file_path: str):
        self.file_path = file_path
        super().__init__(
            message=message,
            code=ErrorCode.DATA_LOAD_ERROR,
            details=f"File: {file_path}",
            user_message="Could not load the data file. Please check if it exists."
        )


class InputValidationError(ChatbotError):
    """Raised when user input fails validation."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.INPUT_TOO_LONG):
        super().__init__(
            message=message,
            code=code,
            user_message=message  # Input validation messages are safe to show
        )

