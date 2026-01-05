"""
Query Processor for Educational Data Chatbot.

Orchestrates the complete pipeline:
Question → Code Generation → Validation → Execution → Response

Developer: aliawada127001@outlook.com
"""

import time
from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from pathlib import Path

import pandas as pd

from config import config
from exceptions import (
    ChatbotError, CodeGenerationError, CodeValidationError,
    CodeExecutionError, DataLoadError, InputValidationError
)
from logger import app_logger
from utils import extract_schema, sanitize_input, format_result_for_display
from code_generator import get_code_generator, get_response_generator, GenerationResult
from code_validator import validate_code, ValidationResult
from code_executor import execute_code, ExecutionResult


@dataclass
class QueryResult:
    """Complete result of a query processing."""
    success: bool
    question: str
    answer: str
    data: Any = None
    data_type: str = "none"
    code: str = ""
    execution_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    total_time_ms: float = 0.0
    error: Optional[str] = None
    error_code: Optional[str] = None
    warnings: list = field(default_factory=list)
    
    @property
    def has_data(self) -> bool:
        """Check if result contains displayable data."""
        return self.data is not None and self.data_type != "none"
    
    @property
    def has_visualization(self) -> bool:
        """Check if result contains a Plotly visualization."""
        return self.data_type == "plotly_figure"
    
    @property
    def is_plotly_figure(self) -> bool:
        """Check if result is a Plotly figure (alias for has_visualization)."""
        return self.data_type == "plotly_figure"


class DataManager:
    """
    Manages data loading and caching.
    
    Implements lazy loading and caching for the DataFrame.
    """
    
    def __init__(self, data_path: Path = None):
        """Initialize with data file path."""
        self.data_path = data_path or config.data_path
        self._df: Optional[pd.DataFrame] = None
        self._schema: Optional[str] = None
    
    def load_data(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Load and cache the DataFrame.
        
        Args:
            force_reload: Force reload even if cached
            
        Returns:
            Loaded DataFrame
        """
        if self._df is None or force_reload:
            try:
                app_logger.info(
                    "Loading data file",
                    path=str(self.data_path)
                )
                
                self._df = pd.read_excel(
                    self.data_path,
                    sheet_name=config.data.sheet_name
                )
                
                app_logger.info(
                    "Data loaded successfully",
                    shape=str(self._df.shape),
                    columns=list(self._df.columns)
                )
                
            except FileNotFoundError:
                raise DataLoadError(
                    message="Data file not found",
                    file_path=str(self.data_path)
                )
            except Exception as e:
                raise DataLoadError(
                    message=f"Error loading data: {str(e)}",
                    file_path=str(self.data_path)
                )
        
        return self._df
    
    def get_schema(self, force_refresh: bool = False) -> str:
        """
        Get or generate DataFrame schema description.
        
        Args:
            force_refresh: Force schema regeneration
            
        Returns:
            Schema description string
        """
        if self._schema is None or force_refresh:
            df = self.load_data()
            self._schema = extract_schema(df)
        
        return self._schema
    
    @property
    def df(self) -> pd.DataFrame:
        """Get the DataFrame (loads if needed)."""
        return self.load_data()
    
    @property
    def schema(self) -> str:
        """Get the schema (generates if needed)."""
        return self.get_schema()


class QueryProcessor:
    """
    Main query processing orchestrator.
    
    Coordinates:
    1. Input validation
    2. Code generation (LLM)
    3. Code validation (security)
    4. Code execution (sandboxed)
    5. Response formatting (LLM)
    """
    
    def __init__(self, data_manager: DataManager = None):
        """Initialize with optional data manager."""
        self.data_manager = data_manager or DataManager()
        self._code_generator = None
        self._response_generator = None
    
    @property
    def code_generator(self):
        """Lazy load code generator."""
        if self._code_generator is None:
            self._code_generator = get_code_generator()
        return self._code_generator
    
    @property
    def response_generator(self):
        """Lazy load response generator."""
        if self._response_generator is None:
            self._response_generator = get_response_generator()
        return self._response_generator
    
    def process_question(self, question: str) -> QueryResult:
        """
        Process a user question through the complete pipeline.
        
        Args:
            question: User's natural language question
            
        Returns:
            QueryResult with answer, data, and metadata
        """
        start_time = time.perf_counter()
        warnings = []
        
        app_logger.info(
            "Processing question",
            question=question[:100]
        )
        
        try:
            # Step 1: Input validation
            question = self._validate_input(question)
            
            # Step 2: Load data and schema
            df = self.data_manager.df
            schema = self.data_manager.schema
            
            # Step 3: Generate code
            gen_result = self._generate_code(question, schema)
            
            if not gen_result.success:
                return self._create_error_result(
                    question=question,
                    error="Could not generate analysis code",
                    error_code="GENERATION_FAILED",
                    start_time=start_time
                )
            
            # Step 4: Validate code
            try:
                val_result = self._validate_code(gen_result.code)
                warnings.extend(val_result.warnings)
            except (CodeValidationError, Exception) as e:
                return self._create_error_result(
                    question=question,
                    error=str(e.user_message if hasattr(e, 'user_message') else e),
                    error_code="VALIDATION_FAILED",
                    start_time=start_time
                )
            
            # Step 5: Execute code
            exec_result = self._execute_code(val_result.sanitized_code, df)
            
            if not exec_result.success:
                return self._create_error_result(
                    question=question,
                    error=exec_result.error or "Execution failed",
                    error_code="EXECUTION_FAILED",
                    start_time=start_time,
                    code=gen_result.code
                )
            
            # Step 6: Format response
            formatted_result, result_type = format_result_for_display(exec_result.result)
            answer = self._generate_response(question, formatted_result, gen_result.code)
            
            total_time = (time.perf_counter() - start_time) * 1000
            
            app_logger.query(question, success=True, duration_ms=total_time)
            
            return QueryResult(
                success=True,
                question=question,
                answer=answer,
                data=exec_result.result,
                data_type=result_type,
                code=gen_result.code,
                execution_time_ms=exec_result.execution_time_ms,
                generation_time_ms=gen_result.generation_time_ms,
                total_time_ms=total_time,
                warnings=warnings
            )
            
        except ChatbotError as e:
            return self._create_error_result(
                question=question,
                error=e.user_message,
                error_code=e.code.name if hasattr(e, 'code') else "ERROR",
                start_time=start_time
            )
            
        except Exception as e:
            app_logger.error(
                "Unexpected error processing question",
                error=str(e),
                error_type=type(e).__name__
            )
            return self._create_error_result(
                question=question,
                error="An unexpected error occurred. Please try again.",
                error_code="UNEXPECTED_ERROR",
                start_time=start_time
            )
    
    def _validate_input(self, question: str) -> str:
        """Validate and sanitize user input."""
        try:
            return sanitize_input(question, config.security.max_input_length)
        except ValueError as e:
            raise InputValidationError(str(e))
    
    def _generate_code(self, question: str, schema: str) -> GenerationResult:
        """Generate pandas code from question."""
        return self.code_generator.generate_from_question(question, schema)
    
    def _validate_code(self, code: str) -> ValidationResult:
        """Validate generated code for security."""
        return validate_code(code)
    
    def _execute_code(self, code: str, df: pd.DataFrame) -> ExecutionResult:
        """Execute validated code."""
        return execute_code(code, df)
    
    def _generate_response(self, question: str, results: str, code: str) -> str:
        """Generate natural language response."""
        try:
            return self.response_generator.generate_response(question, results, code)
        except Exception as e:
            app_logger.warning(
                "Response generation failed",
                error=str(e)
            )
            return f"Here are the results:\n\n{results}"
    
    def _create_error_result(
        self,
        question: str,
        error: str,
        error_code: str,
        start_time: float,
        code: str = ""
    ) -> QueryResult:
        """Create an error result."""
        total_time = (time.perf_counter() - start_time) * 1000
        
        app_logger.query(question, success=False, duration_ms=total_time)
        
        return QueryResult(
            success=False,
            question=question,
            answer=f"Error: {error}",
            error=error,
            error_code=error_code,
            code=code,
            total_time_ms=total_time
        )
    
    def check_system(self) -> Dict[str, bool]:
        """
        Check system health and connectivity.
        
        Returns:
            Dict with component health status
        """
        status = {
            'data_loaded': False,
            'ollama_connected': False,
            'model_available': False,
            'ready': False
        }
        
        # Check data
        try:
            self.data_manager.load_data()
            status['data_loaded'] = True
        except Exception:
            pass
        
        # Check Ollama connection
        try:
            status['ollama_connected'] = self.code_generator.check_connection()
            status['model_available'] = status['ollama_connected']
        except Exception:
            pass
        
        status['ready'] = all([
            status['data_loaded'],
            status['ollama_connected'],
            status['model_available']
        ])
        
        return status


# Global instances
_data_manager: Optional[DataManager] = None
_processor: Optional[QueryProcessor] = None


def get_data_manager() -> DataManager:
    """Get or create the global data manager."""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager


def get_processor() -> QueryProcessor:
    """Get or create the global query processor."""
    global _processor
    if _processor is None:
        _processor = QueryProcessor(get_data_manager())
    return _processor


def process_question(question: str) -> QueryResult:
    """
    Convenience function for processing questions.
    
    Args:
        question: User's question
        
    Returns:
        QueryResult with answer and data
    """
    return get_processor().process_question(question)

