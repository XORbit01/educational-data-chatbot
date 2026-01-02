"""
Utilities for Educational Data Chatbot.

Provides schema extraction, prompt templates, and helper functions.

Developer: aliawada127001@outlook.com
"""

import re
from typing import Tuple, Optional
import pandas as pd


def extract_schema(df: pd.DataFrame) -> str:
    """
    Extract DataFrame schema as a formatted string for LLM context.
    
    Args:
        df: The pandas DataFrame to analyze
        
    Returns:
        Formatted schema description string
    """
    schema_parts = []
    
    # Basic info
    schema_parts.append(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n")
    
    # Column details
    schema_parts.append("Columns:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notna().sum()
        unique = df[col].nunique()
        
        # Sample values (for categorical or string columns)
        if df[col].dtype == 'object' or unique <= 10:
            samples = df[col].dropna().unique()[:5]
            sample_str = f" | Examples: {list(samples)}"
        else:
            sample_str = f" | Range: [{df[col].min()}, {df[col].max()}]"
        
        schema_parts.append(
            f"  - {col}: {dtype} ({non_null} non-null, {unique} unique){sample_str}"
        )
    
    return "\n".join(schema_parts)


def get_column_descriptions() -> str:
    """
    Get human-readable column descriptions for the educational dataset.
    
    Returns:
        Formatted column descriptions
    """
    return """
Column Descriptions:
- student_id: Unique identifier for each student (integer)
- student_name: Student's name (string, format: Student_XXXX)
- student_gender: Gender of the student (M = Male, F = Female)
- class_level: Class/grade level (C1, C2, C3, C4, C5)
- course_name: Subject name (Mathematics, Biology, Computer Science, Chemistry)
- assessment_no: Assessment number (1, 2, 3, etc.)
- assessment_score: Score out of 100 (float)
- raised_hand_count: Number of times student raised hand in class (integer)
- moodle_views: Number of views on Moodle learning platform (integer)
- attendance_rate: Attendance percentage (float, 0-100)
- resources_downloads: Number of learning resources downloaded (integer)
""".strip()


def build_code_generation_prompt(question: str, schema: str) -> str:
    """
    Build the prompt for LLM code generation.
    
    Args:
        question: User's natural language question
        schema: DataFrame schema description
        
    Returns:
        Complete prompt for code generation
    """
    return f"""You are a pandas expert. Generate ONLY executable Python pandas code to answer the user's question.

DATAFRAME SCHEMA:
{schema}

{get_column_descriptions()}

EXAMPLE QUERIES:
1. "Compare course scores" → df.groupby('course_name')['assessment_score'].mean()
2. "Gender performance" → df.groupby('student_gender')['assessment_score'].mean()
3. "Best class level" → df.groupby('class_level')['assessment_score'].mean().idxmax()
4. "Attendance correlation" → df[['attendance_rate', 'assessment_score']].corr()
5. "Top 5 students" → df.groupby('student_id')['assessment_score'].mean().nlargest(5)

USER QUESTION: "{question}"

INSTRUCTIONS:
1. Generate ONLY Python pandas code - no explanations, no markdown
2. Use 'df' as the DataFrame variable name
3. The last line should be the result expression (no print statements)
4. Use only safe pandas/numpy operations
5. Code must be a single expression or a few lines ending with the result

CODE:"""


def build_response_prompt(question: str, results: str, code: str) -> str:
    """
    Build the prompt for natural language response generation.
    
    Args:
        question: Original user question
        results: Execution results as string
        code: The executed code
        
    Returns:
        Prompt for response formatting
    """
    return f"""You are a helpful data analyst assistant. Explain the analysis results in natural, conversational language.

QUESTION: "{question}"

CODE EXECUTED:
{code}

RESULTS:
{results}

INSTRUCTIONS:
1. Provide a clear, concise explanation of what the results mean
2. Highlight key insights and patterns
3. Use specific numbers from the results
4. Keep the response conversational and helpful
5. Format with markdown for readability
6. Do NOT include the code in your response

RESPONSE:"""


def extract_code_from_response(response: str) -> str:
    """
    Extract Python code from LLM response.
    
    Handles various formats:
    - Plain code
    - Markdown code blocks (```python or ```)
    - Mixed text and code
    
    Args:
        response: Raw LLM response
        
    Returns:
        Extracted and cleaned code string
    """
    # Try to extract from markdown code block
    patterns = [
        r'```python\s*\n(.*?)```',  # ```python ... ```
        r'```\s*\n(.*?)```',         # ``` ... ```
        r'```(.*?)```',              # Inline code block
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            code = match.group(1).strip()
            if code:
                return clean_code(code)
    
    # If no code block, try to extract code-like lines
    lines = response.strip().split('\n')
    code_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Skip empty lines, comments that look like prose, and non-code lines
        if not stripped:
            continue
        if stripped.startswith('#') and len(stripped) > 50:
            continue
        if any(stripped.lower().startswith(x) for x in ['here', 'this', 'the ', 'to ', 'i ']):
            continue
        # Likely code if it contains pandas operations or assignments
        if any(x in stripped for x in ['df', 'pd.', 'np.', '=', '.', '(', '[', 'groupby']):
            code_lines.append(stripped)
    
    if code_lines:
        return clean_code('\n'.join(code_lines))
    
    # Last resort: return cleaned response
    return clean_code(response)


def clean_code(code: str) -> str:
    """
    Clean and normalize extracted code.
    
    Args:
        code: Raw code string
        
    Returns:
        Cleaned code string
    """
    # Remove markdown artifacts
    code = re.sub(r'^```\w*\s*', '', code)
    code = re.sub(r'```\s*$', '', code)
    
    # Remove 'CODE:' prefix if present
    code = re.sub(r'^CODE:\s*', '', code, flags=re.IGNORECASE)
    
    # Remove print statements (we capture the result directly)
    code = re.sub(r'\bprint\s*\((.*)\)', r'\1', code)
    
    # Remove leading/trailing whitespace
    code = code.strip()
    
    # Remove any trailing comments that look like explanations
    lines = code.split('\n')
    cleaned_lines = []
    for line in lines:
        # Keep the line but remove trailing explanation comments
        if '#' in line:
            parts = line.split('#')
            # Keep code part and short comments only
            if len(parts[0].strip()) > 0:
                if len(parts) > 1 and len(parts[1]) < 30:
                    cleaned_lines.append(line)
                else:
                    cleaned_lines.append(parts[0].rstrip())
            else:
                # It's a full-line comment - keep if short
                if len(line) < 50:
                    cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()


def format_result_for_display(result) -> Tuple[str, str]:
    """
    Format execution result for display.
    
    Args:
        result: The execution result (DataFrame, Series, scalar, etc.)
        
    Returns:
        Tuple of (formatted_text, result_type)
    """
    if isinstance(result, pd.DataFrame):
        if len(result) > 20:
            display_df = pd.concat([result.head(10), result.tail(10)])
            text = f"Showing first 10 and last 10 of {len(result)} rows:\n{display_df.to_string()}"
        else:
            text = result.to_string()
        return text, "dataframe"
    
    elif isinstance(result, pd.Series):
        if len(result) > 20:
            display_series = pd.concat([result.head(10), result.tail(10)])
            text = f"Showing first 10 and last 10 of {len(result)} items:\n{display_series.to_string()}"
        else:
            text = result.to_string()
        return text, "series"
    
    elif isinstance(result, (int, float)):
        text = str(round(result, 4) if isinstance(result, float) else result)
        return text, "scalar"
    
    elif isinstance(result, (list, tuple)):
        text = str(result)
        return text, "list"
    
    else:
        text = str(result)
        return text, "other"


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input for security.
    
    Args:
        text: Raw user input
        max_length: Maximum allowed length
        
    Returns:
        Sanitized input string
        
    Raises:
        ValueError: If input is too long or contains dangerous patterns
    """
    # Check length
    if len(text) > max_length:
        raise ValueError(f"Input too long. Maximum {max_length} characters allowed.")
    
    # Remove potentially dangerous patterns
    text = text.strip()
    
    # Check for code injection patterns
    dangerous_patterns = [
        r'__\w+__',           # Dunder methods
        r'import\s+\w+',      # Import statements
        r'exec\s*\(',         # exec()
        r'eval\s*\(',         # eval()
        r'open\s*\(',         # open()
        r'os\.\w+',           # os module
        r'sys\.\w+',          # sys module
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Input contains potentially unsafe patterns.")
    
    return text

