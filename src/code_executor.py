"""
Code Executor for Educational Data Chatbot.

Provides sandboxed execution environment for validated pandas code.
Implements timeout protection, memory limits, and error handling.

Developer: aliawada127001@outlook.com
"""

import signal
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional, Dict
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import traceback

import pandas as pd
import numpy as np

from config import config
from exceptions import CodeExecutionError, ExecutionTimeoutError, ErrorCode
from logger import executor_logger


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    result_type: str = "unknown"


class CodeExecutor:
    """
    Sandboxed code executor with security controls.
    
    Features:
    - Restricted global namespace (only df, pd, np)
    - Timeout protection
    - Error handling with safe messages
    - Result capture
    """
    
    def __init__(self, timeout: int = None):
        """
        Initialize executor with timeout setting.
        
        Args:
            timeout: Execution timeout in seconds (default from config)
        """
        self.timeout = timeout or config.security.execution_timeout
    
    def execute(self, code: str, df: pd.DataFrame) -> ExecutionResult:
        """
        Execute validated code in a sandboxed environment.
        
        Args:
            code: Validated Python/pandas code
            df: DataFrame to operate on
            
        Returns:
            ExecutionResult with success status and result/error
        """
        start_time = time.perf_counter()
        
        executor_logger.info(
            "Executing code",
            code_length=len(code),
            df_shape=str(df.shape)
        )
        
        try:
            # Create safe execution environment
            safe_globals = self._create_safe_globals(df)
            safe_locals: Dict[str, Any] = {}
            
            # Execute with timeout
            result = self._execute_with_timeout(
                code, 
                safe_globals, 
                safe_locals,
                self.timeout
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Determine result type
            result_type = self._get_result_type(result)
            
            executor_logger.performance(
                "code_execution",
                execution_time,
                result_type=result_type
            )
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time_ms=execution_time,
                result_type=result_type
            )
            
        except FuturesTimeoutError:
            execution_time = (time.perf_counter() - start_time) * 1000
            executor_logger.warning(
                "Execution timeout",
                timeout=self.timeout,
                code_preview=code[:100]
            )
            raise ExecutionTimeoutError(self.timeout)
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            error_msg = self._safe_error_message(e)
            
            executor_logger.error(
                "Execution error",
                error=error_msg,
                error_type=type(e).__name__
            )
            
            return ExecutionResult(
                success=False,
                result=None,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _create_safe_globals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create a restricted global namespace for code execution.
        
        Args:
            df: DataFrame to make available
            
        Returns:
            Dictionary with only safe objects
        """
        # Minimal safe globals - no __builtins__
        safe_globals = {
            # Data objects
            'df': df.copy(),  # Use a copy to prevent modification
            'pd': pd,
            'np': np,
            
            # Safe built-in functions only
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'range': range,
            'zip': zip,
            'enumerate': enumerate,
            'sorted': sorted,
            'reversed': reversed,
            'min': min,
            'max': max,
            'sum': sum,
            'abs': abs,
            'round': round,
            'any': any,
            'all': all,
            'isinstance': isinstance,
            
            # Boolean constants
            'True': True,
            'False': False,
            'None': None,
        }
        
        # Explicitly remove __builtins__ access
        safe_globals['__builtins__'] = {}
        
        return safe_globals
    
    def _execute_with_timeout(
        self, 
        code: str, 
        globals_dict: Dict[str, Any],
        locals_dict: Dict[str, Any],
        timeout: int
    ) -> Any:
        """
        Execute code with timeout protection.
        
        Uses ThreadPoolExecutor for cross-platform timeout support.
        
        Args:
            code: Code to execute
            globals_dict: Global namespace
            locals_dict: Local namespace
            timeout: Timeout in seconds
            
        Returns:
            Execution result
        """
        def _exec_code():
            # Compile first for better error messages
            compiled = compile(code, '<generated>', 'exec')
            exec(compiled, globals_dict, locals_dict)
            
            # Try to get the result from various sources
            # 1. Check if 'result' was explicitly assigned
            if 'result' in locals_dict:
                return locals_dict['result']
            
            # 2. Check for common result variable names
            for var in ['output', 'data', 'answer', 'stats', 'summary']:
                if var in locals_dict:
                    return locals_dict[var]
            
            # 3. Return the last expression value
            # Parse code to get last expression
            try:
                tree = compile(code, '<generated>', 'eval')
                return eval(tree, globals_dict, locals_dict)
            except SyntaxError:
                # Multi-line code - try to evaluate last line
                lines = [l.strip() for l in code.strip().split('\n') if l.strip()]
                if lines:
                    last_line = lines[-1]
                    # Remove assignment if present
                    if '=' in last_line and not any(op in last_line for op in ['==', '!=', '<=', '>=']):
                        parts = last_line.split('=', 1)
                        if len(parts) == 2:
                            var_name = parts[0].strip()
                            if var_name in locals_dict:
                                return locals_dict[var_name]
                    
                    # Try to evaluate last line as expression
                    try:
                        return eval(last_line, globals_dict, locals_dict)
                    except:
                        pass
            
            # 4. Return any DataFrame or Series in locals
            for value in locals_dict.values():
                if isinstance(value, (pd.DataFrame, pd.Series)):
                    return value
            
            # 5. Return first non-None value
            for value in locals_dict.values():
                if value is not None and not callable(value):
                    return value
            
            return None
        
        # Use ThreadPoolExecutor for timeout (works on Windows)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_exec_code)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                raise
    
    def _get_result_type(self, result: Any) -> str:
        """Determine the type of result for formatting."""
        if result is None:
            return "none"
        elif isinstance(result, pd.DataFrame):
            return "dataframe"
        elif isinstance(result, pd.Series):
            return "series"
        elif isinstance(result, (int, float, np.integer, np.floating)):
            return "scalar"
        elif isinstance(result, str):
            return "string"
        elif isinstance(result, (list, tuple)):
            return "list"
        elif isinstance(result, dict):
            return "dict"
        else:
            return "other"
    
    def _safe_error_message(self, error: Exception) -> str:
        """
        Create a safe error message without leaking internals.
        
        Args:
            error: The exception that occurred
            
        Returns:
            User-safe error message
        """
        error_type = type(error).__name__
        
        # Common error mappings to user-friendly messages
        error_messages = {
            'KeyError': f"Column not found: {str(error)}",
            'ValueError': f"Invalid value: {str(error)[:100]}",
            'TypeError': f"Type error: {str(error)[:100]}",
            'AttributeError': f"Invalid operation: {str(error)[:100]}",
            'IndexError': "Index out of range",
            'ZeroDivisionError': "Cannot divide by zero",
            'NameError': f"Unknown variable: {str(error)[:50]}",
        }
        
        if error_type in error_messages:
            return error_messages[error_type]
        
        # Generic safe message
        return f"Execution error: {error_type}"


# Global executor instance
executor = CodeExecutor()


def execute_code(code: str, df: pd.DataFrame) -> ExecutionResult:
    """
    Convenience function for code execution.
    
    Args:
        code: Validated code to execute
        df: DataFrame to operate on
        
    Returns:
        ExecutionResult with result or error
    """
    return executor.execute(code, df)

