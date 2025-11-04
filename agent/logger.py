"""
Structured logging configuration for the Accessibility Testing Agent.
Provides consistent logging with levels, formatting, and rotation.
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON-structured logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, "url"):
            log_data["url"] = record.url
        if hasattr(record, "device_type"):
            log_data["device_type"] = record.device_type
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "retry_count"):
            log_data["retry_count"] = record.retry_count
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    EMOJI = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        emoji = self.EMOJI.get(record.levelname, '')
        reset = self.RESET
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Build log message
        message = f"{color}{emoji} [{timestamp}] {record.levelname:8s}{reset} | {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logger(
    name: str = "accessibility_agent",
    log_level: str = "INFO",
    log_dir: Optional[str] = "logs",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = False
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_console: Enable console output with colors
        enable_file: Enable file output
        enable_json: Enable JSON file output
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColoredConsoleFormatter())
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file and log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Regular text log
        file_handler = RotatingFileHandler(
            log_path / f"{name}.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # JSON file handler
    if enable_json and log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        json_handler = RotatingFileHandler(
            log_path / f"{name}.json",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        logger.addHandler(json_handler)
    
    return logger


class PerformanceLogger:
    """Context manager for performance logging."""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.extra = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting: {self.operation}", extra=self.extra)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"Completed: {self.operation} in {duration:.2f}s",
                extra={**self.extra, "duration": duration}
            )
        else:
            self.logger.error(
                f"Failed: {self.operation} after {duration:.2f}s",
                extra={**self.extra, "duration": duration, "error_type": exc_type.__name__}
            )
        
        return False  # Don't suppress exceptions


# Create default logger
default_logger = setup_logger()


def log_test_start(logger: logging.Logger, url: str, device_type: str, tab_index: int):
    """Log the start of a test."""
    logger.info(
        f"Tab-{tab_index+1}: Starting test",
        extra={"url": url, "device_type": device_type, "tab_index": tab_index}
    )


def log_test_complete(logger: logging.Logger, url: str, violations_count: int, duration: float, tab_index: int):
    """Log successful test completion."""
    logger.info(
        f"Tab-{tab_index+1}: Test completed - {violations_count} violations found",
        extra={
            "url": url,
            "violations_count": violations_count,
            "duration": duration,
            "tab_index": tab_index
        }
    )


def log_test_error(logger: logging.Logger, url: str, error: Exception, retry_count: int, tab_index: int):
    """Log test error with retry information."""
    logger.error(
        f"Tab-{tab_index+1}: Test failed - {type(error).__name__}: {str(error)}",
        extra={
            "url": url,
            "error_type": type(error).__name__,
            "retry_count": retry_count,
            "tab_index": tab_index
        },
        exc_info=True
    )


def log_retry_attempt(logger: logging.Logger, url: str, attempt: int, max_retries: int, error: Exception):
    """Log retry attempt."""
    logger.warning(
        f"Retry {attempt}/{max_retries} for {url} - Previous error: {type(error).__name__}",
        extra={
            "url": url,
            "retry_count": attempt,
            "max_retries": max_retries,
            "error_type": type(error).__name__
        }
    )
