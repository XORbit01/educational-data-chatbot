"""
Code Generator for Educational Data Chatbot.

Interfaces with Ollama to run DeepSeek Coder 6.7B locally
for generating pandas code from natural language questions.
100% offline operation.

Developer: aliawada127001@outlook.com
"""

import time
from dataclasses import dataclass
from typing import Optional

import ollama
from ollama import Client

from config import config
from exceptions import CodeGenerationError, ErrorCode
from logger import llm_logger
from utils import extract_code_from_response, build_code_generation_prompt


@dataclass
class GenerationResult:
    """Result of code generation."""
    success: bool
    code: str
    raw_response: str
    generation_time_ms: float
    model: str
    error: Optional[str] = None


class CodeGenerator:
    """
    LLM-based code generator using Ollama/DeepSeek Coder.
    
    Features:
    - 100% offline operation via Ollama
    - DeepSeek Coder 6.7B for pandas code generation
    - Automatic code extraction from responses
    - Retry logic for failed generations
    """
    
    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        temperature: float = None,
        timeout: int = None
    ):
        """
        Initialize the code generator.
        
        Args:
            model: Ollama model name (default: deepseek-coder:6.7b)
            base_url: Ollama server URL (default: localhost:11434)
            temperature: Generation temperature (default: 0.1)
            timeout: Request timeout in seconds
        """
        self.model = model or config.llm.model_name
        self.base_url = base_url or config.llm.base_url
        self.temperature = temperature if temperature is not None else config.llm.temperature
        self.timeout = timeout or config.llm.timeout
        
        # Initialize Ollama client
        self.client = Client(host=self.base_url)
        
        llm_logger.info(
            "Code generator initialized",
            model=self.model,
            base_url=self.base_url
        )
    
    def generate(self, prompt: str, max_retries: int = 2) -> GenerationResult:
        """
        Generate pandas code from a prompt.
        
        Args:
            prompt: Complete prompt with schema and question
            max_retries: Number of retries on failure
            
        Returns:
            GenerationResult with generated code
        """
        start_time = time.perf_counter()
        last_error = None
        previous_errors = []  # Track errors to detect loops
        original_prompt = prompt  # Keep original for reference
        
        for attempt in range(max_retries + 1):
            try:
                llm_logger.info(
                    "Generating code",
                    attempt=attempt + 1,
                    prompt_length=len(prompt)
                )
                
                # Call Ollama API
                response = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    options={
                        'temperature': self.temperature,
                        'num_predict': config.llm.max_tokens,
                    }
                )
                
                raw_response = response.get('response', '')
                
                if not raw_response:
                    raise CodeGenerationError(
                        message="Empty response from LLM",
                        code=ErrorCode.LLM_INVALID_RESPONSE
                    )
                
                # Log raw response for debugging
                llm_logger.debug(
                    "Raw LLM response",
                    response_preview=raw_response[:500],
                    response_length=len(raw_response),
                    attempt=attempt + 1
                )
                
                # Extract code from response
                code = extract_code_from_response(raw_response)
                
                # Log extracted code for debugging
                llm_logger.debug(
                    "Extracted code",
                    code_preview=code[:500] if code else "None",
                    code_length=len(code) if code else 0,
                    attempt=attempt + 1
                )
                
                if not code or len(code.strip()) < 5:
                    llm_logger.error(
                        "Code extraction failed",
                        raw_response=raw_response[:500],
                        extracted_code=code[:200] if code else "None"
                    )
                    raise CodeGenerationError(
                        message="Could not extract valid code from response",
                        code=ErrorCode.CODE_EXTRACTION_FAILED,
                        details=raw_response[:200]
                    )
                
                # Validate syntax - if error, retry with feedback
                syntax_error = self._validate_syntax(code)
                if syntax_error and attempt < max_retries:
                    # Check if we're getting the same error (infinite loop detection)
                    if syntax_error in previous_errors:
                        llm_logger.error(
                            "Same syntax error repeated - stopping retry loop",
                            error=syntax_error,
                            previous_errors=previous_errors,
                            attempt=attempt + 1
                        )
                        raise CodeGenerationError(
                            message=f"Syntax error persists after retries: {syntax_error}",
                            code=ErrorCode.CODE_EXTRACTION_FAILED,
                            details=code[:500]
                        )
                    
                    previous_errors.append(syntax_error)
                    
                    llm_logger.warning(
                        "Syntax error detected, retrying with feedback",
                        error=syntax_error,
                        attempt=attempt + 1,
                        code_preview=code[:300]
                    )
                    # Build retry prompt with syntax error feedback
                    prompt = self._build_syntax_error_retry_prompt(original_prompt, code, syntax_error, previous_errors)
                    continue  # Retry with new prompt
                
                if syntax_error:
                    # Final attempt failed with syntax error
                    raise CodeGenerationError(
                        message=f"Syntax error in generated code: {syntax_error}",
                        code=ErrorCode.CODE_EXTRACTION_FAILED,
                        details=code[:500]
                    )
                
                generation_time = (time.perf_counter() - start_time) * 1000
                
                llm_logger.performance(
                    "code_generation",
                    generation_time,
                    code_length=len(code),
                    response_length=len(raw_response)
                )
                
                return GenerationResult(
                    success=True,
                    code=code,
                    raw_response=raw_response,
                    generation_time_ms=generation_time,
                    model=self.model
                )
                
            except ollama.ResponseError as e:
                last_error = f"Ollama error: {str(e)}"
                llm_logger.warning(
                    "Ollama response error",
                    attempt=attempt + 1,
                    error=str(e)
                )
                
            except ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                llm_logger.error(
                    "Cannot connect to Ollama",
                    error=str(e)
                )
                raise CodeGenerationError(
                    message="Cannot connect to Ollama. Is it running?",
                    code=ErrorCode.LLM_CONNECTION_ERROR,
                    details=str(e)
                )
                
            except CodeGenerationError:
                raise
                
            except Exception as e:
                last_error = str(e)
                llm_logger.warning(
                    "Generation attempt failed",
                    attempt=attempt + 1,
                    error=str(e)
                )
        
        # All retries failed
        generation_time = (time.perf_counter() - start_time) * 1000
        
        llm_logger.error(
            "Code generation failed after retries",
            retries=max_retries,
            last_error=last_error
        )
        
        return GenerationResult(
            success=False,
            code="",
            raw_response="",
            generation_time_ms=generation_time,
            model=self.model,
            error=last_error
        )
    
    def _validate_syntax(self, code: str) -> Optional[str]:
        """
        Validate code syntax.
        
        Args:
            code: Code string to validate
            
        Returns:
            Error message if syntax error, None if valid
        """
        import ast
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"{e.msg} (line {e.lineno}, offset {e.offset})"
    
    def _build_syntax_error_retry_prompt(self, original_prompt: str, broken_code: str, error: str, previous_errors: list = None) -> str:
        """
        Build a retry prompt that includes syntax error feedback.
        
        Args:
            original_prompt: Original generation prompt
            broken_code: The code that had syntax errors
            error: The syntax error message
            previous_errors: List of previous errors (to show pattern)
            
        Returns:
            New prompt with error feedback
        """
        # Extract the user question from original prompt
        user_question = ""
        if 'USER QUESTION:' in original_prompt:
            try:
                question_part = original_prompt.split('USER QUESTION:')[1].split('CRITICAL')[0].strip().strip('"')
                user_question = question_part
            except:
                user_question = "See original request"
        else:
            user_question = "Generate the requested code"
        
        # Extract specific error details and fix instructions
        error_details = ""
        fix_example = ""
        
        if "unterminated string literal" in error.lower():
            error_details = "UNTERMINATED STRING LITERAL - A string starts with a quote (single ' or double \") but doesn't have a matching closing quote."
            # Show example based on what we see in the broken code
            if "color='" in broken_code:
                fix_example = """
EXAMPLE OF THE FIX NEEDED:
BROKEN: marker=dict(color='
FIXED:  marker=dict(color='#FF6B6B')

The string color=' is incomplete - you need to add a value and close the quote.
"""
            else:
                fix_example = """
EXAMPLE OF THE FIX NEEDED:
BROKEN: some_variable = 'incomplete
FIXED:  some_variable = 'complete'

Find any string that starts with ' or " but doesn't end with the same quote, and close it.
"""
        elif "invalid syntax" in error.lower():
            error_details = "INVALID SYNTAX - Check for missing commas, parentheses, brackets, or quotes."
        
        # Build warning if this is a repeat
        repeat_warning = ""
        if previous_errors and len(previous_errors) > 1:
            repeat_warning = "\n⚠️ WARNING: This error occurred before. Make sure you're actually fixing it, not repeating the same mistake!\n"
        
        return f"""You are a pandas and Plotly expert. Fix the syntax error in the code below.

ORIGINAL REQUEST: {user_question}

BROKEN CODE (HAS SYNTAX ERROR - DO NOT REPEAT):
```python
{broken_code}
```

SYNTAX ERROR: {error}
{error_details}
{fix_example}
{repeat_warning}
CRITICAL INSTRUCTIONS:
1. The code above is BROKEN - it will NOT work
2. Find the syntax error and fix it completely
3. For unterminated strings: add a value and close the quote (e.g., color='#FF6B6B' not color=')
4. Generate ONLY the FIXED code - no explanations, no markdown blocks, no comments
5. The fixed code must be valid Python that can be executed
6. Every string must have matching opening and closing quotes

Generate the FIXED code:"""
    
    def generate_from_question(
        self, 
        question: str, 
        schema: str
    ) -> GenerationResult:
        """
        Generate code from a user question and DataFrame schema.
        
        Args:
            question: User's natural language question
            schema: DataFrame schema description
            
        Returns:
            GenerationResult with generated code
        """
        prompt = build_code_generation_prompt(question, schema)
        return self.generate(prompt)
    
    def check_connection(self) -> bool:
        """
        Check if Ollama is running and model is available.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try using ollama.list() directly (simpler API)
            try:
                models_response = ollama.list()
            except Exception:
                # Fallback to client.list()
                models_response = self.client.list()
            
            # Debug: log the response type
            llm_logger.debug(
                "Ollama list response",
                response_type=type(models_response).__name__,
                response_preview=str(models_response)[:200]
            )
            
            # Handle different possible response formats
            available_models = []
            
            # The ollama.list() returns a dict with 'models' key
            if isinstance(models_response, dict):
                models_list = models_response.get('models', [])
                if not models_list and 'models' not in models_response:
                    # Maybe the response itself is the list
                    models_list = models_response if isinstance(models_response, list) else []
            elif isinstance(models_response, list):
                models_list = models_response
            else:
                models_list = []
            
            # Extract model names
            for model in models_list:
                if isinstance(model, dict):
                    # Try different possible keys that Ollama might use
                    name = (
                        model.get('name') or 
                        model.get('model') or 
                        model.get('model_name') or
                        ''
                    )
                elif isinstance(model, str):
                    name = model
                else:
                    continue
                
                # Only add non-empty names
                if name and name.strip():
                    available_models.append(name.strip())
            
            # Debug: log what we found
            llm_logger.debug(
                "Parsed models",
                count=len(available_models),
                models=available_models[:5]
            )
            
            # Check if our model is available
            # Match exact name or base name (e.g., "deepseek-coder:6.7b" or "deepseek-coder")
            model_base = self.model.split(':')[0]
            model_available = any(
                self.model == m or 
                m == self.model or
                m.startswith(model_base + ':') or
                (':' not in m and m == model_base)
                for m in available_models
            )
            
            if not model_available:
                # Fallback: Try to show the model directly (sometimes list() doesn't work but model exists)
                try:
                    model_info = self.client.show(self.model)
                    if model_info:
                        llm_logger.info(
                            "Model found via show() method",
                            model=self.model
                        )
                        return True
                except Exception:
                    pass
                
                llm_logger.warning(
                    "Model not found",
                    model=self.model,
                    available=available_models[:5] if available_models else [],
                    model_base=model_base
                )
                return False
            
            llm_logger.info(
                "Ollama connection successful",
                model=self.model,
                available_models=len(available_models)
            )
            return True
            
        except Exception as e:
            llm_logger.error(
                "Ollama connection failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return False
    
    def get_model_info(self) -> Optional[dict]:
        """
        Get information about the current model.
        
        Returns:
            Model information dict or None
        """
        try:
            return self.client.show(self.model)
        except Exception:
            return None


class ResponseGenerator:
    """
    Generates natural language responses from execution results.
    
    Uses the same LLM to format results into human-readable responses.
    """
    
    def __init__(self, code_generator: CodeGenerator = None):
        """Initialize with existing code generator or create new one."""
        self.generator = code_generator or CodeGenerator()
    
    def generate_response(
        self, 
        question: str, 
        results: str, 
        code: str
    ) -> str:
        """
        Generate a natural language response explaining the results.
        
        Args:
            question: Original user question
            results: Execution results as string
            code: The executed code
            
        Returns:
            Natural language explanation
        """
        from utils import build_response_prompt
        
        prompt = build_response_prompt(question, results, code)
        
        try:
            result = self.generator.generate(prompt)
            
            if result.success:
                # Clean up the response
                response = result.raw_response.strip()
                # Remove any code blocks that might have been included
                if '```' in response:
                    # Keep only text before first code block
                    parts = response.split('```')
                    response = parts[0].strip()
                    if len(parts) > 2:
                        # Add text after last code block
                        response += '\n' + parts[-1].strip()
                
                return response if response else self._fallback_response(results)
            else:
                return self._fallback_response(results)
                
        except Exception as e:
            llm_logger.warning(
                "Response generation failed, using fallback",
                error=str(e)
            )
            return self._fallback_response(results)
    
    def _fallback_response(self, results: str) -> str:
        """Generate a basic fallback response."""
        return f"Here are the results of your analysis:\n\n{results}"


# Global instances
_generator: Optional[CodeGenerator] = None
_response_generator: Optional[ResponseGenerator] = None


def get_code_generator() -> CodeGenerator:
    """Get or create the global code generator."""
    global _generator
    if _generator is None:
        _generator = CodeGenerator()
    return _generator


def get_response_generator() -> ResponseGenerator:
    """Get or create the global response generator."""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator(get_code_generator())
    return _response_generator


def generate_code(question: str, schema: str) -> GenerationResult:
    """
    Convenience function for code generation.
    
    Args:
        question: User's question
        schema: DataFrame schema
        
    Returns:
        GenerationResult with generated code
    """
    return get_code_generator().generate_from_question(question, schema)

