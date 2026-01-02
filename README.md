# Educational Data Chatbot

A secure, 100% offline chatbot for querying educational data using natural language. Powered by DeepSeek Coder 6.7B running locally via Ollama.

**Academic Project - Lebanese University**

**Developer:** aliawada127001@outlook.com

## Overview

This application enables users to analyze student performance data through natural language queries. The system dynamically generates pandas code using a local LLM, validates it through multi-layer security, executes it in a sandboxed environment, and returns formatted insights with interactive visualizations.

### Key Features

- **100% Offline Operation** - All processing happens locally, no internet required
- **Natural Language Queries** - Ask questions in plain English
- **Dynamic Code Generation** - DeepSeek Coder 6.7B generates pandas code on-the-fly
- **Multi-Layer Security** - AST-based validation, allowlist/denylist enforcement, sandboxed execution
- **Interactive Visualizations** - Automatic chart generation with Plotly
- **Modern UI** - Streamlit-based interface with dark theme
- **Zero API Costs** - Complete privacy, no external services

## Project Structure

```
project_chatbot/
├── src/                        # Source code
│   ├── __init__.py
│   ├── app.py                  # Streamlit main application
│   ├── config.py               # Configuration management
│   ├── logger.py               # Logging system
│   ├── exceptions.py           # Custom exceptions
│   ├── utils.py                # Utility functions
│   ├── query_processor.py      # Query processing pipeline
│   ├── code_generator.py       # LLM code generation
│   ├── code_validator.py       # Security validation
│   ├── code_executor.py        # Sandboxed execution
│   └── response_formatter.py   # Response formatting & visualization
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_validator.py
│   ├── test_executor.py
│   └── test_integration.py
├── data/                       # Data files
│   └── Students_Dataset.xlsx
├── env/                        # Virtual environment (not in git)
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── README.md
└── .gitignore
```

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface"
        UI[Streamlit UI]
    end
    
    subgraph "Application Layer"
        QP[Query Processor]
        CG[Code Generator]
        CV[Code Validator]
        CE[Code Executor]
        RF[Response Formatter]
    end
    
    subgraph "LLM Layer - 100% Offline"
        OLLAMA[Ollama Runtime<br/>localhost:11434]
        MODEL[DeepSeek Coder 6.7B<br/>Local Model]
    end
    
    subgraph "Data Layer"
        EXCEL[Excel File]
        DF[DataFrame]
    end
    
    subgraph "Security Layer"
        AST[AST Parser]
        ALLOW[Allowlist]
        DENY[Denylist]
        SANDBOX[Sandbox]
    end
    
    UI --> QP
    QP --> CG
    CG --> OLLAMA
    OLLAMA --> MODEL
    MODEL --> CV
    CV --> AST
    AST --> ALLOW
    AST --> DENY
    ALLOW --> CE
    DENY --> CE
    CE --> SANDBOX
    SANDBOX --> DF
    DF --> RF
    RF --> UI
    
    EXCEL --> DF
    
    style OLLAMA fill:#2196F3
    style MODEL fill:#4CAF50
    style AST fill:#FF9800
    style ALLOW fill:#4CAF50
    style DENY fill:#F44336
    style SANDBOX fill:#FF9800
```

### Complete Request Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant QP as Query Processor
    participant CG as Code Generator
    participant Ollama as Ollama Runtime
    participant DeepSeek as DeepSeek Coder 6.7B
    participant CV as Code Validator
    participant CE as Code Executor
    participant RF as Response Formatter
    
    User->>UI: "Compare Biology vs CS scores"
    UI->>QP: Process question
    QP->>QP: Load DataFrame & Extract Schema
    QP->>CG: Generate code prompt
    CG->>Ollama: Send prompt (localhost)
    Ollama->>DeepSeek: Run inference
    DeepSeek-->>Ollama: Generated code
    Ollama-->>CG: Code string
    CG->>CV: Validate code
    CV->>CV: Parse AST
    CV->>CV: Check allowlist/denylist
    CV-->>CG: Validated code
    CG->>CE: Execute code
    CE->>CE: Run in sandbox
    CE-->>CG: Results
    CG->>RF: Format response
    RF->>RF: Generate visualization
    RF->>Ollama: Generate explanation
    Ollama->>DeepSeek: Run inference
    DeepSeek-->>Ollama: Natural language
    Ollama-->>RF: Explanation
    RF-->>UI: Complete response
    UI-->>User: Display answer + chart
```

### Component Architecture

#### 1. Query Processor (`query_processor.py`)
- Orchestrates the complete pipeline
- Loads and manages DataFrame
- Builds schema context for LLM
- Generates prompts with examples
- Coordinates all components

#### 2. Code Generator (`code_generator.py`)
- Interfaces with Ollama runtime
- Sends prompts to DeepSeek Coder 6.7B
- Extracts code from LLM responses
- Handles retries and error recovery
- Manages model connection

#### 3. Code Validator (`code_validator.py`)
- Parses code to Abstract Syntax Tree (AST)
- Extracts operations, imports, variables
- Validates against allowlist (approved operations)
- Blocks dangerous operations via denylist
- Handles greylist (unknown operations)
- Pattern-based validation

#### 4. Code Executor (`code_executor.py`)
- Creates sandboxed execution environment
- Restricted globals (only df, pd, np)
- No `__builtins__` access
- Timeout protection (10 seconds)
- Memory limits
- Safe error handling

#### 5. Response Formatter (`response_formatter.py`)
- Formats execution results
- Generates Plotly visualizations
- Creates natural language explanations
- Detects appropriate chart types
- Handles different data types

#### 6. Streamlit UI (`app.py`)
- Modern chat interface
- Message history management
- Interactive visualizations
- Code display (expandable)
- System status monitoring

## Security Architecture

### Multi-Layer Defense

```mermaid
graph TD
    A[User Input] --> B[Layer 1: Input Sanitization]
    B --> C[Layer 2: Code Extraction]
    C --> D[Layer 3: AST Analysis]
    D --> E[Layer 4: Allowlist Validation]
    D --> F[Layer 5: Denylist Protection]
    D --> G[Layer 6: Greylist Handling]
    E --> H[Layer 7: Sandbox Execution]
    F --> H
    G --> H
    H --> I[Safe Results]
    
    style B fill:#E3F2FD
    style C fill:#E3F2FD
    style D fill:#FFF3E0
    style E fill:#E8F5E9
    style F fill:#FFEBEE
    style G fill:#FFF9C4
    style H fill:#F3E5F5
    style I fill:#E8F5E9
```

### Security Layers

1. **Input Sanitization**
   - Validates input length (max 1000 chars)
   - Checks for dangerous patterns
   - Sanitizes special characters

2. **Code Extraction**
   - Extracts code from markdown blocks
   - Removes comments and explanations
   - Cleans formatting

3. **AST Analysis**
   - Parses code to Abstract Syntax Tree
   - Extracts all operations, imports, variables
   - Deep analysis before execution

4. **Allowlist Validation** (Default-Deny)
   - Only approved operations allowed
   - Categories: groupby, mean, sum, filter, merge, corr, etc.
   - Prevents zero-day exploits

5. **Denylist Protection** (Defense-in-Depth)
   - Blocks dangerous operations
   - Examples: eval, exec, import, open, os, sys, subprocess
   - Catches known threats

6. **Greylist Handling**
   - Unknown operations require verification
   - Pattern-based approval
   - Audit logging

7. **Sandbox Execution**
   - Restricted globals (only df, pd, np)
   - No `__builtins__` access
   - Timeout protection (10 seconds)
   - Memory limits
   - Exception isolation

### Security Validation Flow

```mermaid
flowchart TD
    A[Generated Code] --> B{Parse AST}
    B --> C{Check Imports}
    C -->|Found| D[BLOCKED]
    C -->|None| E{Extract Operations}
    E --> F{Check Allowlist}
    F -->|In Allowlist| G{Check Denylist}
    F -->|Not in Allowlist| H{Check Greylist}
    H -->|Pattern Match| G
    H -->|Unknown| I[WARNING]
    G -->|In Denylist| D
    G -->|Not in Denylist| J{Variable Check}
    J -->|Only df/pd/np| K[APPROVED]
    J -->|Other vars| L{Pattern Match}
    L -->|Safe pattern| K
    L -->|Dangerous| D
    K --> M[Execute in Sandbox]
    D --> N[Return Error]
    I --> O[Log & Continue]
    
    style D fill:#FFCDD2
    style K fill:#C8E6C9
    style M fill:#FFF9C4
    style N fill:#FFCDD2
```

## Technology Stack

| Component | Technology | Purpose | Offline Status |
|-----------|-----------|---------|----------------|
| UI Framework | Streamlit | Web interface | ✅ 100% Local |
| Data Processing | Pandas | Data manipulation | ✅ 100% Local |
| LLM Runtime | Ollama | Local LLM server | ✅ 100% Local |
| LLM Model | DeepSeek Coder 6.7B | Code generation | ✅ 100% Local |
| Excel Reader | openpyxl | Read Excel files | ✅ 100% Local |
| Visualization | Plotly | Interactive charts | ✅ 100% Local |
| Code Analysis | AST (built-in) | Security validation | ✅ 100% Local |

### Ollama vs DeepSeek Coder

**Ollama** is the runtime infrastructure (local server) that:
- Manages model loading and execution
- Provides local API endpoints (localhost:11434)
- Handles GPU/CPU optimization
- Manages memory

**DeepSeek Coder 6.7B** is the actual AI model that:
- Runs inside Ollama runtime
- Generates pandas code from prompts
- Processes all requests locally
- Never connects to internet

**Relationship**: Ollama (runtime) → Runs → DeepSeek Coder 6.7B (model)

## Data Flow

```mermaid
flowchart TD
    A[Excel File<br/>Students_Dataset.xlsx] --> B[Load into Memory]
    B --> C[Pandas DataFrame<br/>2,680 rows × 11 columns]
    C --> D[Query Processor<br/>Extract Schema]
    D --> E[Code Execution<br/>Sandbox Environment]
    E --> F[Results<br/>DataFrame/Series/Scalar]
    F --> G[Response Formatter]
    G --> H[Visualization<br/>Plotly Chart]
    G --> I[Natural Language<br/>LLM Explanation]
    H --> J[UI Display]
    I --> J
    
    style A fill:#E1F5FF
    style C fill:#E8F5E9
    style E fill:#FFF3E0
    style F fill:#F3E5F5
    style H fill:#E3F2FD
    style I fill:#E3F2FD
    style J fill:#2196F3
```

## Requirements

### Hardware

- CPU: 4+ cores (8+ recommended)
- RAM: 16GB minimum (32GB recommended)
- Storage: 20GB free space
- GPU: Optional but recommended (NVIDIA with 8GB+ VRAM)

### Software

- Python 3.9+
- Ollama
- DeepSeek Coder 6.7B model

## Installation

### 1. Install Ollama

Download and install Ollama from [ollama.ai](https://ollama.ai/).

**Windows**: Add Ollama to PATH if not automatically added:
```powershell
# If Ollama is at: C:\Users\<username>\AppData\Local\Programs\Ollama\ollama.exe
$env:Path += ";C:\Users\<username>\AppData\Local\Programs\Ollama"
```

### 2. Pull the DeepSeek Coder Model

```bash
ollama pull deepseek-coder:6.7b
```

### 3. Set Up Python Environment

```bash
# Create virtual environment
python -m venv env

# Activate environment
# Windows:
env\Scripts\activate
# macOS/Linux:
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Verify Data File

Ensure `Students_Dataset.xlsx` is in the `data/` directory.

## Usage

### Start Ollama

```bash
ollama serve
```

### Run the Application

```bash
streamlit run run.py
```

The application will open in your default browser at `http://localhost:8501`.

### Example Queries

- "Compare average scores across all courses"
- "How do male vs female students perform?"
- "Which class level has the highest scores?"
- "Is there a correlation between attendance and scores?"
- "Show me the top 10 performing students"
- "What's the average score in Computer Science?"

## Execution Example

**Input:**
```
"Compare average scores across all courses"
```

**Generated Code:**
```python
df.groupby('course_name')['assessment_score'].mean()
```

**Validation:**
- ✅ groupby: in allowlist
- ✅ mean: in allowlist
- ✅ No imports: pass
- ✅ No dangerous operations: pass

**Execution:**
```python
# Sandbox environment
df = loaded_dataframe
result = df.groupby('course_name')['assessment_score'].mean()
# Returns: Series with course names and average scores
```

**Output:**
- Natural language: "The average scores across courses are: Biology 78.5, Computer Science 82.3..."
- Visualization: Bar chart comparing courses
- Data table: Expandable table with results

## Configuration

Edit `src/config.py` to customize:

- **LLM Settings** - Model name, temperature, timeout
- **Security Settings** - Allowed/blocked operations, execution limits
- **UI Settings** - Page title, theme, chart settings

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## Dataset Schema

The `Students_Dataset.xlsx` file contains:

| Column | Type | Description |
|--------|------|-------------|
| student_id | int | Unique student identifier |
| student_name | string | Student's name |
| student_gender | string | Gender (M/F) |
| class_level | string | Class level (C1-C5) |
| course_name | string | Course name |
| assessment_no | int | Assessment number |
| assessment_score | float | Score out of 100 |
| raised_hand_count | int | Times hand raised |
| moodle_views | int | Moodle platform views |
| attendance_rate | float | Attendance percentage |
| resources_downloads | int | Resources downloaded |

**Statistics**: 2,680 rows × 11 columns

## Performance

| Stage | Expected Time | Notes |
|-------|--------------|-------|
| Code Generation | 2-5 seconds | Depends on GPU |
| Code Validation | <100ms | AST parsing is fast |
| Code Execution | <1 second | Most queries are fast |
| Response Formatting | 1-3 seconds | LLM formatting |
| **Total** | **5-10 seconds** | End-to-end |

## Troubleshooting

### Ollama Connection Failed

1. Ensure Ollama is running: `ollama serve`
2. Check if the model is installed: `ollama list`
3. Pull the model if missing: `ollama pull deepseek-coder:6.7b`
4. Verify Ollama is in PATH (Windows)

### Data File Not Found

Ensure `Students_Dataset.xlsx` is in the `data/` directory.

### Slow Response Times

- Use a GPU for faster inference
- Consider model quantization
- Reduce query complexity

### Memory Issues

- Ensure 16GB+ RAM available
- Close other applications
- Consider using a smaller model

## Offline Operation

- **Ollama**: Runs locally on localhost:11434
- **DeepSeek Coder**: Model loaded in memory
- **All Processing**: Local machine only
- **No Internet**: Required only for initial setup
- **No API Calls**: Zero external dependencies

## Error Handling

1. **Code Generation Fails**
   - Retry with simpler prompt
   - Return user-friendly error

2. **Validation Fails**
   - Show security violation message
   - Suggest rephrasing question

3. **Execution Fails**
   - Capture error safely
   - Return helpful message
   - Log for debugging

4. **Timeout**
   - Stop execution after 10 seconds
   - Suggest simpler query

## License

This project is provided for educational purposes.

## Academic Affiliation

This project is part of **Academic Lebanese University**.

## Acknowledgments

- Lebanese University for academic support
- Ollama for local LLM runtime
- DeepSeek for the Coder model
- Streamlit for the UI framework
