"""
Utilities for Educational Data Chatbot.

Provides schema extraction, prompt templates, and helper functions.

Developer: aliawada127001@outlook.com
"""

import re
import ast
from typing import Tuple, Optional
import pandas as pd
import plotly.graph_objects as go

from logger import app_logger


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
IMPORTANT DATA STRUCTURE:
- Each student has MULTIPLE rows (one per course/assessment combination)
- student_id uniquely identifies a student
- When counting students by attributes (gender, class_level), use drop_duplicates('student_id') FIRST to get unique students

Column Descriptions:
- student_id: Unique identifier for each student (integer) - USE THIS FOR DISTINCT STUDENT COUNTS
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


def get_visualization_examples_short() -> str:
    """
    Get concise visualization examples (when user didn't explicitly ask for visualization).
    
    Returns:
        Short visualization reference
    """
    return """
VISUALIZATION REFERENCE (only use if user explicitly asks for charts):
- Use px.bar(), px.pie(), px.scatter(), px.histogram(), px.heatmap() for quick charts
- Use go.Figure() with go.Bar(), go.Pie(), go.Scatter() for advanced customization
- Always set title, labels, and colors. End with 'fig' variable.
""".strip()


def get_visualization_examples_short() -> str:
    """
    Get concise visualization examples (when user didn't explicitly ask for visualization).
    
    Returns:
        Short visualization reference
    """
    return """
VISUALIZATION REFERENCE (only use if user explicitly asks for charts):
- Use px.bar(), px.pie(), px.scatter(), px.histogram(), px.heatmap() for quick charts
- Use go.Figure() with go.Bar(), go.Pie(), go.Scatter() for advanced customization
- Always set title, labels, and colors. End with 'fig' variable.
""".strip()


def get_visualization_examples() -> str:
    """
    Get Plotly visualization examples for the LLM.
    
    Returns:
        Formatted visualization examples
    """
    return """
VISUALIZATION EXAMPLES (use when user asks for charts, graphs, plots, or visual analysis):

1. "Show gender distribution pie chart":
data = df.drop_duplicates('student_id')['student_gender'].value_counts()
fig = go.Figure(data=[go.Pie(
    labels=data.index, values=data.values,
    hole=0.4, marker=dict(colors=['#FF6B6B', '#4ECDC4']),
    textinfo='percent+label', textfont_size=14,
    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>'
)])
fig.update_layout(title='Gender Distribution', font=dict(family='Inter'), showlegend=True)
fig

2. "Compare course scores with beautiful bar chart":
data = df.groupby('course_name')['assessment_score'].mean().sort_values(ascending=True)
fig = go.Figure(data=[go.Bar(
    x=data.values, y=data.index, orientation='h',
    marker=dict(color=data.values, colorscale='Viridis', showscale=True),
    text=[f'{v:.1f}' for v in data.values], textposition='outside'
)])
fig.update_layout(title='Average Scores by Course', xaxis_title='Score', height=400)
fig

3. "Show correlation heatmap":
numeric_cols = ['assessment_score', 'attendance_rate', 'raised_hand_count', 'moodle_views', 'resources_downloads']
corr = df[numeric_cols].corr()
fig = go.Figure(data=go.Heatmap(
    z=corr.values, x=corr.columns, y=corr.columns,
    colorscale='RdBu_r', zmid=0, text=corr.values.round(2), texttemplate='%{text}',
    hovertemplate='%{x} vs %{y}<br>Correlation: %{z:.2f}<extra></extra>'
))
fig.update_layout(title='Correlation Matrix', height=500)
fig

4. "Show score distribution histogram":
fig = go.Figure(data=[go.Histogram(
    x=df['assessment_score'], nbinsx=20,
    marker=dict(color='#667eea', line=dict(color='white', width=1)),
    hovertemplate='Score: %{x}<br>Count: %{y}<extra></extra>'
)])
fig.update_layout(title='Score Distribution', xaxis_title='Score', yaxis_title='Frequency', bargap=0.1)
fig

5. "Show class performance with box plot":
fig = go.Figure()
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
for i, level in enumerate(sorted(df['class_level'].unique())):
    fig.add_trace(go.Box(y=df[df['class_level']==level]['assessment_score'], name=level, marker_color=colors[i % len(colors)]))
fig.update_layout(title='Score Distribution by Class Level', yaxis_title='Score', showlegend=False)
fig

6. "Show attendance vs score scatter plot":
fig = px.scatter(df, x='attendance_rate', y='assessment_score', color='course_name',
    trendline='ols', opacity=0.6, color_discrete_sequence=px.colors.qualitative.Set2,
    hover_data=['student_name', 'class_level'])
fig.update_layout(title='Attendance vs Score Correlation', xaxis_title='Attendance Rate (%)', yaxis_title='Assessment Score')
fig

7. "Show multi-metric radar chart for courses":
courses = df.groupby('course_name').agg({
    'assessment_score': 'mean', 'attendance_rate': 'mean',
    'raised_hand_count': 'mean', 'moodle_views': 'mean'
}).reset_index()
fig = go.Figure()
for _, row in courses.iterrows():
    fig.add_trace(go.Scatterpolar(
        r=[row['assessment_score']/100, row['attendance_rate']/100, row['raised_hand_count']/50, row['moodle_views']/100],
        theta=['Score', 'Attendance', 'Participation', 'Moodle Views'],
        fill='toself', name=row['course_name']
    ))
fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), title='Course Performance Radar')
fig

8. "Show sunburst chart of students by class and gender":
data = df.drop_duplicates('student_id').groupby(['class_level', 'student_gender']).size().reset_index(name='count')
fig = px.sunburst(data, path=['class_level', 'student_gender'], values='count',
    color='count', color_continuous_scale='Blues', title='Student Distribution Sunburst')
fig

9. "Show animated bar chart race of top students":
top_students = df.groupby(['student_id', 'course_name'])['assessment_score'].mean().reset_index()
fig = px.bar(top_students.nlargest(10, 'assessment_score'), x='assessment_score', y='student_id',
    color='course_name', orientation='h', color_discrete_sequence=px.colors.qualitative.Pastel,
    title='Top 10 Student Scores')
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig

10. "Show gauge chart for average score":
avg_score = df['assessment_score'].mean()
fig = go.Figure(go.Indicator(
    mode='gauge+number+delta', value=avg_score, delta={'reference': 70},
    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#667eea'},
           'steps': [{'range': [0, 50], 'color': '#FF6B6B'}, {'range': [50, 70], 'color': '#FFEAA7'}, {'range': [70, 100], 'color': '#4ECDC4'}],
           'threshold': {'line': {'color': 'red', 'width': 4}, 'thickness': 0.75, 'value': 70}}
))
fig.update_layout(title='Average Assessment Score')
fig
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
    # Check if user asks for visualization to conditionally include examples
    # Must be VERY strict - only if user explicitly uses visualization words
    question_lower = question.lower()
    asks_for_viz = (
        any(kw in question_lower for kw in ['visualize', 'visualization', 'visual', 'chart', 'graph', 'plot']) or
        any(pattern in question_lower for pattern in [
            'show me a chart', 'show me a graph', 'create a chart', 'create a graph',
            'pie chart', 'bar chart', 'histogram', 'heatmap', 'scatter plot', 'box plot', 'line chart'
        ])
    )
    
    # Only include full visualization examples if user asks for visualization
    viz_examples = get_visualization_examples() if asks_for_viz else get_visualization_examples_short()
    
    return f"""You are a pandas and Plotly expert. Generate Python code to answer the user's question.

CRITICAL DECISION: WHEN TO USE VISUALIZATIONS
- ONLY generate Plotly figures (fig) if the user EXPLICITLY uses these words:
  * "visualize", "visualization", "visual", "chart", "graph", "plot"
  * "show me a chart", "create a chart", "display as chart", "draw a chart"
  * Specific chart types: "pie chart", "bar chart", "histogram", "heatmap", "scatter plot", etc.
- For ALL OTHER questions (who, what, how many, compare, find, list, top, best, etc.):
  * Return DATA only (DataFrame, Series, or scalar value)
  * DO NOT create any Plotly figures - NO fig, NO px, NO go!
  * Examples: "Who are the top 10 students?" → return DataFrame, NOT a chart
  * Examples: "Who is the best student?" → return data, NOT a chart
  * Examples: "How many students?" → return number, NOT a chart
  * Examples: "Compare scores" → return comparison data, NOT a chart
  * Examples: "List top performers" → return data, NOT a chart
  * ONLY if user says "visualize the top 10" or "show me a chart of top 10" → THEN create chart

DATAFRAME SCHEMA:
{schema}

{get_column_descriptions()}

AVAILABLE LIBRARIES:
- df: The pandas DataFrame with student data
- pd: pandas library
- np: numpy library  
- px: plotly.express (ONLY use when user asks for visualization)
- go: plotly.graph_objects (ONLY use when user asks for visualization)

COLOR PALETTES (ONLY for visualizations):
- Vibrant: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
- Gradient: 'Viridis', 'Plasma', 'Inferno', 'Magma', 'Cividis', 'Blues', 'RdBu_r'
- Qualitative: px.colors.qualitative.Set2, px.colors.qualitative.Pastel

DATA ANALYSIS EXAMPLES (NO VISUALIZATIONS - just return data):
1. "How many males/females" → df.drop_duplicates('student_id')['student_gender'].value_counts()
2. "Who is the best student?" → 
   df = df.drop_duplicates('student_id')
   best_student = df.groupby('student_id')['assessment_score'].mean().nlargest(1).index[0]
   result = df[df['student_id'] == best_student][['student_id', 'student_name', 'assessment_score']]
   result
   # NOTE: NO fig, NO px, NO go - just return the data!
3. "Who are the top 10 students?" → 
   df = df.drop_duplicates('student_id')
   top_10 = df.groupby('student_id')['assessment_score'].mean().nlargest(10)
   result = df[df['student_id'].isin(top_10.index)][['student_id', 'student_name', 'assessment_score']].drop_duplicates('student_id')
   result
   # NOTE: NO fig, NO px, NO go - just return the data!
4. "What is the average score?" → df['assessment_score'].mean()
5. "Compare course scores" → df.groupby('course_name')['assessment_score'].mean()
6. "Top 5 students" → df.groupby('student_id')['assessment_score'].mean().nlargest(5)
7. "Attendance correlation" → df[['attendance_rate', 'assessment_score']].corr()
8. "List all students" → df.drop_duplicates('student_id')[['student_id', 'student_name']]

{viz_examples}

USER QUESTION: "{question}"

CRITICAL RULES (MUST FOLLOW):
- DO NOT use import statements (px, go, pd, np, df are already available)
- DO NOT use lambda functions
- DO NOT use exec, eval, open, or any file operations
- The libraries px, go, pd, np are PRE-IMPORTED and ready to use
- Generate COMPLETE, VALID Python code - all strings must be properly closed
- All parentheses, brackets, and quotes must be balanced
- Code must be syntactically correct and executable

INSTRUCTIONS:
1. Generate ONLY Python code - no explanations, no markdown, no comments
2. Use 'df' as the DataFrame variable name
3. DECISION: Does the user explicitly use words like "visualize", "chart", "graph", "plot", "visualization"?
   - YES (user said "visualize X" or "show me a chart of X") → Create Plotly figure (fig) with beautiful, colorful, professional charts
   - NO (user said "who are", "what are", "list", "top 10", "best students", etc.) → Return data only (DataFrame, Series, or scalar) - NO fig, NO px, NO go, NO Plotly code at all!
4. CRITICAL EXAMPLES:
   - "Who are the top 10 students?" → NO visualization, just return DataFrame
   - "Visualize the top 10 students" → YES, create chart
   - "Show me top performers" → NO visualization, just return data
   - "Show me a chart of top performers" → YES, create chart
5. If creating visualization: add meaningful titles, labels, and hover information
6. If creating visualization: use modern color schemes and clean layouts
7. For counting students: use drop_duplicates('student_id') FIRST
8. NEVER write import statements - all libraries are already imported
9. ENSURE all strings are properly closed with matching quotes (use 'text' or "text", not mixed quotes!)
10. ENSURE all parentheses and brackets are balanced
11. The last line should be: 'fig' (if visualization) OR 'result'/'data' (if data analysis)
12. CRITICAL: If user does NOT say "visualize", "chart", "graph", or "plot" → NO VISUALIZATIONS, just data!

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
    app_logger.debug(
        "Extracting code from LLM response",
        response_length=len(response),
        response_preview=response[:300]
    )
    
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
                app_logger.debug(
                    "Found code in markdown block",
                    pattern=pattern[:30],
                    code_preview=code[:300],
                    code_length=len(code)
                )
                cleaned = clean_code(code)
                app_logger.debug(
                    "Code after cleaning",
                    cleaned_preview=cleaned[:300],
                    cleaned_length=len(cleaned)
                )
                # Don't auto-fix syntax errors - let the generator retry with feedback
                return cleaned
    
    # If no code block, try to extract code-like lines
    lines = response.strip().split('\n')
    code_lines = []
    
    # Patterns that indicate instruction text, not code
    instruction_patterns = [
        r'^- ',  # Lines starting with "- " (bullet points)
        r'DO NOT', r'MUST FOLLOW', r'CRITICAL', r'INSTRUCTIONS', r'RULES',
        r'NOTE:', r'IMPORTANT:', r'WARNING:', r'EXAMPLE:',
        r'use when', r'only use if', r'if user', r'when user',
        r'–', r'—',  # En-dash and em-dash (common in instructions)
    ]
    
    for line in lines:
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            continue
        
        # Skip lines that look like instructions
        if any(re.search(pattern, stripped, re.IGNORECASE) for pattern in instruction_patterns):
            continue
        
        # Skip comments that look like prose
        if stripped.startswith('#') and len(stripped) > 50:
            continue
        
        # Skip lines that start with prose-like words
        if any(stripped.lower().startswith(x) for x in ['here', 'this', 'the ', 'to ', 'i ', 'you ', 'we ']):
            continue
        
        # Skip lines that are clearly not code (too many words, no code patterns)
        words = stripped.split()
        if len(words) > 10 and not any(x in stripped for x in ['df', 'pd.', 'np.', 'px.', 'go.', '=', '.', '(', '[', 'groupby', 'import']):
            continue
        
        # Likely code if it contains pandas operations or assignments
        if any(x in stripped for x in ['df', 'pd.', 'np.', 'px.', 'go.', '=', '.', '(', '[', 'groupby', 'import']):
            code_lines.append(stripped)
    
    if code_lines:
        cleaned = clean_code('\n'.join(code_lines))
        return cleaned
    
    # Last resort: return cleaned response
    cleaned = clean_code(response)
    return cleaned


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
    
    # Remove lines that look like instructions (bullet points, rules, etc.)
    lines = code.split('\n')
    cleaned_lines = []
    instruction_patterns = [
        r'^- ',  # Lines starting with "- "
        r'DO NOT', r'MUST FOLLOW', r'CRITICAL', r'INSTRUCTIONS', r'RULES',
        r'NOTE:', r'IMPORTANT:', r'WARNING:', r'EXAMPLE:',
        r'use when', r'only use if', r'if user', r'when user',
    ]
    
    for line in lines:
        stripped = line.strip()
        # Skip instruction-like lines
        if any(re.search(pattern, stripped, re.IGNORECASE) for pattern in instruction_patterns):
            continue
        # Skip lines with Unicode dashes (en-dash, em-dash) that aren't in strings
        if re.search(r'[–—]', stripped) and not (stripped.startswith("'") or stripped.startswith('"')):
            continue
        cleaned_lines.append(line)
    
    code = '\n'.join(cleaned_lines)
    
    # Remove leading/trailing whitespace
    code = code.strip()
    
    # Fix common syntax issues
    # 1. Try to fix unterminated strings by checking quote balance
    lines = code.split('\n')
    
    # Simple check: count quotes in the entire code
    # This is a heuristic - if there's an odd number of quotes, try to close them
    all_code = '\n'.join(lines)
    
    # Count unescaped quotes
    single_quotes = 0
    double_quotes = 0
    i = 0
    while i < len(all_code):
        if all_code[i] == '\\' and i + 1 < len(all_code):
            i += 2  # Skip escaped character
            continue
        if all_code[i] == "'":
            single_quotes += 1
        elif all_code[i] == '"':
            double_quotes += 1
        i += 1
    
    # If there's an unmatched quote, try to close it at the end
    if single_quotes % 2 != 0 and lines:
        # Check if last line already ends with a quote
        last_line = lines[-1].rstrip()
        if not last_line.endswith("'") and not last_line.endswith('\\'):
            lines[-1] = lines[-1] + "'"
    elif double_quotes % 2 != 0 and lines:
        # Check if last line already ends with a quote
        last_line = lines[-1].rstrip()
        if not last_line.endswith('"') and not last_line.endswith('\\'):
            lines[-1] = lines[-1] + '"'
    
    # Remove any trailing comments that look like explanations
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
        result: The execution result (DataFrame, Series, scalar, Plotly figure, etc.)
        
    Returns:
        Tuple of (formatted_text, result_type)
    """
    # Check for Plotly figure first
    if isinstance(result, go.Figure):
        # For Plotly figures, return a description
        title = result.layout.title.text if result.layout.title and result.layout.title.text else "Visualization"
        num_traces = len(result.data) if result.data else 0
        text = f"📊 {title} ({num_traces} data series)"
        return text, "plotly_figure"
    
    elif isinstance(result, pd.DataFrame):
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

