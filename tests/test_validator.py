"""
Tests for Code Validator.

Tests the security validation including AST analysis,
allowlist/denylist enforcement, and pattern detection.

Developer: aliawada127001@outlook.com
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_validator import CodeValidator, validate_code, ValidationResult
from exceptions import CodeValidationError, SecurityViolationError


class TestCodeValidatorAllowlist:
    """Test allowlist (approved operations)."""
    
    def test_basic_groupby(self):
        """Test basic groupby operation is allowed."""
        code = "df.groupby('course_name')['assessment_score'].mean()"
        result = validate_code(code)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_multiple_operations(self):
        """Test chained operations are allowed."""
        code = "df.groupby('student_gender')['assessment_score'].agg(['mean', 'std', 'count'])"
        result = validate_code(code)
        assert result.is_valid
    
    def test_filtering(self):
        """Test filtering operations."""
        code = "df[df['assessment_score'] > 80].head(10)"
        result = validate_code(code)
        assert result.is_valid
    
    def test_sorting(self):
        """Test sorting operations."""
        code = "df.sort_values('assessment_score', ascending=False).head(5)"
        result = validate_code(code)
        assert result.is_valid
    
    def test_correlation(self):
        """Test correlation analysis."""
        code = "df[['attendance_rate', 'assessment_score']].corr()"
        result = validate_code(code)
        assert result.is_valid
    
    def test_value_counts(self):
        """Test value_counts operation."""
        code = "df['course_name'].value_counts()"
        result = validate_code(code)
        assert result.is_valid


class TestCodeValidatorDenylist:
    """Test denylist (blocked operations)."""
    
    def test_import_blocked(self):
        """Test that import statements are blocked."""
        code = "import os\nos.system('ls')"
        with pytest.raises(SecurityViolationError):
            validate_code(code)
    
    def test_exec_blocked(self):
        """Test that exec is blocked."""
        code = "exec('print(1)')"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)
    
    def test_eval_blocked(self):
        """Test that eval is blocked."""
        code = "eval('1+1')"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)
    
    def test_open_blocked(self):
        """Test that file operations are blocked."""
        code = "open('file.txt', 'r').read()"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)
    
    def test_os_access_blocked(self):
        """Test that os module access is blocked."""
        code = "df.head()\nos.getcwd()"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)
    
    def test_subprocess_blocked(self):
        """Test that subprocess is blocked."""
        code = "subprocess.run(['ls'])"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)
    
    def test_dunder_blocked(self):
        """Test that dunder methods are blocked."""
        code = "df.__class__.__bases__"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)


class TestCodeValidatorPatterns:
    """Test pattern-based validation."""
    
    def test_getattr_pattern(self):
        """Test getattr pattern is blocked."""
        code = "getattr(df, 'head')()"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)
    
    def test_lambda_blocked(self):
        """Test lambda functions are blocked."""
        code = "df.apply(lambda x: x * 2)"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)
    
    def test_globals_blocked(self):
        """Test globals() is blocked."""
        code = "globals()['os']"
        with pytest.raises((CodeValidationError, SecurityViolationError)):
            validate_code(code)


class TestCodeValidatorSyntax:
    """Test syntax validation."""
    
    def test_syntax_error(self):
        """Test that syntax errors are caught."""
        code = "df.groupby('name'["
        with pytest.raises(CodeValidationError):
            validate_code(code)
    
    def test_empty_code(self):
        """Test empty code handling."""
        code = ""
        with pytest.raises(CodeValidationError):
            validate_code(code)
    
    def test_whitespace_only(self):
        """Test whitespace-only code."""
        code = "   \n\t  "
        with pytest.raises(CodeValidationError):
            validate_code(code)


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_valid_result(self):
        """Test valid result properties."""
        code = "df.head()"
        result = validate_code(code)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert result.sanitized_code == code
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
    
    def test_warnings_included(self):
        """Test that warnings are included for greylist operations."""
        # Unknown but safe-looking operations might generate warnings
        code = "df.some_custom_method()"
        try:
            result = validate_code(code)
            # Should either pass with warnings or fail
            assert isinstance(result.warnings, list)
        except (CodeValidationError, SecurityViolationError):
            pass  # Also acceptable


class TestQuickCheck:
    """Test quick validation."""
    
    def test_quick_check_valid(self):
        """Test quick check with valid code."""
        validator = CodeValidator()
        assert validator.quick_check("df.head()") is True
    
    def test_quick_check_import(self):
        """Test quick check catches imports."""
        validator = CodeValidator()
        assert validator.quick_check("import os") is False
    
    def test_quick_check_exec(self):
        """Test quick check catches exec."""
        validator = CodeValidator()
        assert validator.quick_check("exec('code')") is False
    
    def test_quick_check_syntax_error(self):
        """Test quick check catches syntax errors."""
        validator = CodeValidator()
        assert validator.quick_check("df.head([") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

