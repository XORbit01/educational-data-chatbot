"""
Integration Tests for Educational Data Chatbot.

Tests the complete pipeline from question to result.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'student_id': range(1000, 1010),
        'student_name': [f'Student_{i}' for i in range(1000, 1010)],
        'student_gender': ['M', 'F'] * 5,
        'class_level': ['C1', 'C2', 'C3', 'C4', 'C5'] * 2,
        'course_name': ['Mathematics', 'Biology', 'Computer Science', 'Chemistry'] * 2 + ['Mathematics', 'Biology'],
        'assessment_no': [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
        'assessment_score': [85.0, 78.0, 92.0, 88.0, 76.0, 82.0, 90.0, 85.0, 79.0, 88.0],
        'raised_hand_count': [14, 18, 22, 15, 20, 16, 19, 21, 17, 23],
        'moodle_views': [42, 35, 50, 38, 45, 40, 48, 36, 41, 52],
        'attendance_rate': [95.0, 85.0, 90.0, 92.0, 88.0, 94.0, 91.0, 87.0, 93.0, 89.0],
        'resources_downloads': [20, 15, 25, 18, 22, 19, 24, 16, 21, 27]
    })


class TestUtilsFunctions:
    """Test utility functions."""
    
    def test_extract_schema(self, sample_df):
        """Test schema extraction."""
        from utils import extract_schema
        
        schema = extract_schema(sample_df)
        
        assert 'student_id' in schema
        assert 'assessment_score' in schema
        assert 'Columns:' in schema
    
    def test_sanitize_input_valid(self):
        """Test valid input sanitization."""
        from utils import sanitize_input
        
        result = sanitize_input("What is the average score?")
        assert result == "What is the average score?"
    
    def test_sanitize_input_too_long(self):
        """Test input that's too long."""
        from utils import sanitize_input
        
        long_input = "a" * 1001
        with pytest.raises(ValueError):
            sanitize_input(long_input, max_length=1000)
    
    def test_sanitize_input_dangerous(self):
        """Test dangerous input patterns."""
        from utils import sanitize_input
        
        with pytest.raises(ValueError):
            sanitize_input("import os; os.system('rm -rf /')")
    
    def test_extract_code_from_response(self):
        """Test code extraction from LLM response."""
        from utils import extract_code_from_response
        
        response = """
        Here's the code:
        ```python
        df.groupby('course_name')['assessment_score'].mean()
        ```
        """
        
        code = extract_code_from_response(response)
        assert 'groupby' in code
        assert 'mean' in code
    
    def test_format_result_dataframe(self, sample_df):
        """Test formatting DataFrame result."""
        from utils import format_result_for_display
        
        text, result_type = format_result_for_display(sample_df)
        
        assert result_type == 'dataframe'
        assert 'student_id' in text
    
    def test_format_result_scalar(self):
        """Test formatting scalar result."""
        from utils import format_result_for_display
        
        text, result_type = format_result_for_display(85.5)
        
        assert result_type == 'scalar'
        assert '85.5' in text


class TestCodeValidatorIntegration:
    """Integration tests for code validator."""
    
    def test_valid_complex_query(self):
        """Test complex but valid query."""
        from code_validator import validate_code
        
        code = """
result = df.groupby(['course_name', 'class_level'])['assessment_score'].agg(['mean', 'std', 'count'])
result.reset_index()
"""
        result = validate_code(code)
        assert result.is_valid
    
    def test_invalid_with_import(self):
        """Test that import is blocked."""
        from code_validator import validate_code
        from exceptions import SecurityViolationError
        
        code = """
import pandas as pd
df.head()
"""
        with pytest.raises(SecurityViolationError):
            validate_code(code)


class TestCodeExecutorIntegration:
    """Integration tests for code executor."""
    
    def test_complex_aggregation(self, sample_df):
        """Test complex aggregation."""
        from code_executor import execute_code
        
        code = """
result = df.groupby('course_name').agg({
    'assessment_score': ['mean', 'std'],
    'attendance_rate': 'mean'
})
result
"""
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.DataFrame)
    
    def test_correlation_matrix(self, sample_df):
        """Test correlation calculation."""
        from code_executor import execute_code
        
        code = "df[['assessment_score', 'attendance_rate', 'raised_hand_count']].corr()"
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.DataFrame)
        assert result.result.shape == (3, 3)
    
    def test_filtered_aggregation(self, sample_df):
        """Test filtering followed by aggregation."""
        from code_executor import execute_code
        
        code = """
filtered = df[df['assessment_score'] > 80]
filtered.groupby('student_gender')['assessment_score'].mean()
"""
        result = execute_code(code, sample_df)
        
        assert result.success
        assert isinstance(result.result, pd.Series)


class TestVisualizationGeneration:
    """Test visualization generation."""
    
    def test_bar_chart_detection(self):
        """Test bar chart detection."""
        from response_formatter import ChartDetector
        import pandas as pd
        
        data = pd.Series([85, 78, 92], index=['Math', 'Science', 'English'])
        chart_type = ChartDetector.detect_chart_type(data, "Compare course scores")
        
        assert chart_type == 'bar'
    
    def test_scatter_detection(self):
        """Test scatter plot detection."""
        from response_formatter import ChartDetector
        import pandas as pd
        
        data = pd.DataFrame({
            'attendance': [90, 85, 95],
            'score': [85, 78, 92]
        })
        chart_type = ChartDetector.detect_chart_type(data, "correlation between attendance and scores")
        
        assert chart_type in ['scatter', 'heatmap']
    
    def test_visualization_generation(self, sample_df):
        """Test actual visualization generation."""
        from response_formatter import generate_visualization
        
        data = sample_df.groupby('course_name')['assessment_score'].mean()
        result = generate_visualization(data, "Compare course scores")
        
        assert result.chart_type == 'bar'
        assert result.figure is not None


class TestEndToEndPipeline:
    """End-to-end pipeline tests (requires Ollama running)."""
    
    @pytest.mark.skip(reason="Requires Ollama to be running")
    def test_full_pipeline(self, sample_df):
        """Test complete query processing pipeline."""
        from query_processor import QueryProcessor, DataManager
        
        # Create a mock data manager
        class MockDataManager(DataManager):
            def __init__(self, df):
                self._df = df
                self._schema = None
            
            def load_data(self, force_reload=False):
                return self._df
        
        data_manager = MockDataManager(sample_df)
        processor = QueryProcessor(data_manager)
        
        result = processor.process_question("What is the average assessment score?")
        
        assert result is not None
        # Further assertions depend on LLM response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

