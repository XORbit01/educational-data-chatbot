# Educational Data Chatbot

A secure, offline chatbot for querying educational data using natural language. Powered by DeepSeek Coder 6.7B running locally via Ollama.

## Overview

This application allows users to analyze student performance data through natural language queries. The system generates pandas code dynamically, validates it for security, executes it in a sandboxed environment, and returns formatted insights with visualizations.

### Key Features

- **100% Offline Operation** - All processing happens locally, no internet required
- **Natural Language Queries** - Ask questions in plain English
- **Dynamic Code Generation** - DeepSeek Coder 6.7B generates pandas code on-the-fly
- **Multi-Layer Security** - AST-based validation, allowlist/denylist enforcement, sandboxed execution
- **Interactive Visualizations** - Automatic chart generation with Plotly
- **Modern UI** - Streamlit-based interface with dark theme

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
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   └── PRE_CODING_CHECKLIST.md
├── env/                        # Virtual environment (not in git)
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── README.md
└── .gitignore
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

## Architecture

### Pipeline Flow

1. **User Input** - Natural language question
2. **Query Processor** - Orchestrates the pipeline
3. **Code Generator** - LLM generates pandas code
4. **Code Validator** - Security validation (AST analysis, allowlist/denylist)
5. **Code Executor** - Sandboxed execution with timeout
6. **Response Formatter** - Natural language response with visualization

### Security Layers

1. **Input Sanitization** - Validate and sanitize user input
2. **AST Analysis** - Parse generated code to Abstract Syntax Tree
3. **Allowlist Validation** - Only approved pandas operations allowed
4. **Denylist Protection** - Block dangerous operations (exec, eval, file I/O, etc.)
5. **Sandbox Execution** - Restricted globals, no builtins access
6. **Timeout Protection** - Prevent infinite loops

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

## Troubleshooting

### Ollama Connection Failed

1. Ensure Ollama is running: `ollama serve`
2. Check if the model is installed: `ollama list`
3. Pull the model if missing: `ollama pull deepseek-coder:6.7b`

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

## License

This project is provided for educational purposes.

## Acknowledgments

- Ollama for local LLM runtime
- DeepSeek for the Coder model
- Streamlit for the UI framework
