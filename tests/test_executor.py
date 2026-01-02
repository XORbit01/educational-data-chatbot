"""
Tests for Code Executor.

Tests the sandboxed execution environment including
timeout protection, safe globals, and error handling.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_executor import CodeExecutor, execute_code, ExecutionResult
from exceptions import ExecutionTimeoutError


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'student_id': [1, 2, 3, 4, 5],
        'student_name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'course_name': ['Math', 'Science', 'Math', 'Science', 'Math'],
        'assessment_score': [85.0, 78.0, 92.0, 88.0, 76.0],
        'attendance_rate': [95.0, 85.0, 90.0, 92.0, 88.0]
    })


class TestCodeExecutorBasic:
    """Test basic execution functionality."""
    
    def test_simple_head(self, sample_df):
        """Test simple head() operation."""
        code = "df.head(3)"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.DataFrame)
        assert len(result.result) == 3
    
    def test_groupby_mean(self, sample_df):
        """Test groupby with mean."""
        code = "df.groupby('course_name')['assessment_score'].mean()"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.Series)
        assert len(result.result) == 2  # Math and Science
    
    def test_filtering(self, sample_df):
        """Test filtering operation."""
        code = "df[df['assessment_score'] > 80]"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.DataFrame)
        assert all(result.result['assessment_score'] > 80)
    
    def test_scalar_result(self, sample_df):
        """Test operation returning scalar."""
        code = "df['assessment_score'].mean()"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, (int, float, np.number))
    
    def test_correlation(self, sample_df):
        """Test correlation calculation."""
        code = "df[['assessment_score', 'attendance_rate']].corr()"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.DataFrame)
        assert result.result.shape == (2, 2)


class TestCodeExecutorSandbox:
    """Test sandbox security."""
    
    def test_no_builtins_access(self, sample_df):
        """Test that __builtins__ is not accessible."""
        code = "__builtins__"
        result = execute_code(code, sample_df)
        
        # Should either fail or return empty dict
        if result.success:
            assert result.result == {} or result.result is None
    
    def test_df_is_copy(self, sample_df):
        """Test that DataFrame is copied (original not modified)."""
        original_len = len(sample_df)
        
        code = "df.drop(0, inplace=True)\ndf"
        result = execute_code(code, sample_df)
        
        # Original should be unchanged
        assert len(sample_df) == original_len
    
    def test_safe_builtins_available(self, sample_df):
        """Test that safe builtins are available."""
        code = "len(df)"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert result.result == 5
    
    def test_pandas_available(self, sample_df):
        """Test that pd is available."""
        code = "pd.DataFrame({'a': [1, 2, 3]})"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.DataFrame)
    
    def test_numpy_available(self, sample_df):
        """Test that np is available."""
        code = "np.mean(df['assessment_score'].values)"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, (float, np.floating))


class TestCodeExecutorErrorHandling:
    """Test error handling."""
    
    def test_syntax_error(self, sample_df):
        """Test handling of syntax errors."""
        code = "df.head(["
        result = execute_code(code, sample_df)
        
        assert not result.success
        assert result.error is not None
    
    def test_key_error(self, sample_df):
        """Test handling of KeyError."""
        code = "df['nonexistent_column']"
        result = execute_code(code, sample_df)
        
        assert not result.success
        assert 'Column not found' in result.error or 'nonexistent' in result.error
    
    def test_type_error(self, sample_df):
        """Test handling of TypeError."""
        code = "df['student_name'] + 5"
        result = execute_code(code, sample_df)
        
        assert not result.success
        assert result.error is not None
    
    def test_division_by_zero(self, sample_df):
        """Test handling of division by zero."""
        code = "1 / 0"
        result = execute_code(code, sample_df)
        
        assert not result.success
        assert 'zero' in result.error.lower()


class TestCodeExecutorTimeout:
    """Test timeout protection."""
    
    def test_fast_execution(self, sample_df):
        """Test that fast operations complete."""
        executor = CodeExecutor(timeout=5)
        result = executor.execute("df.head()", sample_df)
        
        assert result.success
        assert result.execution_time_ms < 5000
    
    def test_execution_time_recorded(self, sample_df):
        """Test that execution time is recorded."""
        result = execute_code("df.describe()", sample_df)
        
        assert result.execution_time_ms >= 0


class TestExecutionResult:
    """Test ExecutionResult dataclass."""
    
    def test_success_result(self, sample_df):
        """Test successful result properties."""
        result = execute_code("df.head()", sample_df)
        
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.result is not None
        assert result.error is None
        assert result.execution_time_ms >= 0
        assert result.result_type in ['dataframe', 'series', 'scalar', 'list', 'dict', 'other']
    
    def test_failure_result(self, sample_df):
        """Test failed result properties."""
        result = execute_code("df['bad_col']", sample_df)
        
        assert isinstance(result, ExecutionResult)
        assert result.success is False
        assert result.error is not None


class TestMultilineCode:
    """Test multi-line code execution."""
    
    def test_assignment_and_return(self, sample_df):
        """Test assignment followed by expression."""
        code = """
result = df.groupby('course_name')['assessment_score'].mean()
result
"""
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.Series)
    
    def test_multiple_operations(self, sample_df):
        """Test multiple chained operations."""
        code = """
filtered = df[df['assessment_score'] > 80]
grouped = filtered.groupby('course_name').size()
grouped
"""
        result = execute_code(code, sample_df)
        
        assert result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

