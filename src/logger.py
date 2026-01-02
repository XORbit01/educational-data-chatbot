"""
Logging System for Educational Data Chatbot.

Provides structured logging for application, security, and performance events.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ChatbotLogger:
    """Centralized logging for the chatbot application."""
    
    # Log format with timestamp, level, and structured message
    LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    _instances: dict = {}
    
    def __new__(cls, name: str, log_file: Optional[str] = None):
        """Singleton pattern per logger name."""
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        """Initialize logger with optional file output."""
        if hasattr(self, '_initialized'):
            return
            
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Console handler (INFO and above)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(
                logging.Formatter(self.LOG_FORMAT, self.DATE_FORMAT)
            )
            self.logger.addHandler(console_handler)
            
            # File handler (DEBUG and above) - optional
            if log_file:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_path)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(
                    logging.Formatter(self.LOG_FORMAT, self.DATE_FORMAT)
                )
                self.logger.addHandler(file_handler)
        
        self._initialized = True
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def security(self, message: str, **kwargs):
        """Log security-related event (always WARNING level)."""
        self.logger.warning(f"[SECURITY] {self._format_message(message, **kwargs)}")
    
    def performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics."""
        self.logger.info(
            f"[PERF] {operation} completed in {duration_ms:.2f}ms "
            f"{self._format_message('', **kwargs)}"
        )
    
    def query(self, question: str, success: bool, duration_ms: float):
        """Log query execution."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"[QUERY] {status} | {duration_ms:.2f}ms | {question[:50]}..."
        )
    
    @staticmethod
    def _format_message(message: str, **kwargs) -> str:
        """Format message with additional context."""
        if kwargs:
            context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} | {context}" if message else context
        return message


# Pre-configured loggers for different components
def get_logger(name: str) -> ChatbotLogger:
    """Get or create a logger for the specified component."""
    return ChatbotLogger(name)


# Component-specific loggers
app_logger = get_logger("app")
security_logger = get_logger("security")
llm_logger = get_logger("llm")
executor_logger = get_logger("executor")

