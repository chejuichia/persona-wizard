"""Logging configuration for Persona Wizard backend."""

import logging
import sys
from typing import Any, Dict

from .config import settings


def setup_logging() -> None:
    """Set up logging configuration."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    if settings.log_format == "json":
        # JSON logging for production
        import json
        import time
        
        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_entry = {
                    "timestamp": time.time(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                
                # Add extra fields
                for key, value in record.__dict__.items():
                    if key not in ("name", "msg", "args", "levelname", "levelno", "pathname", 
                                 "filename", "module", "lineno", "funcName", "created", 
                                 "msecs", "relativeCreated", "thread", "threadName", 
                                 "processName", "process", "getMessage", "exc_info", 
                                 "exc_text", "stack_info"):
                        log_entry[key] = value
                
                return json.dumps(log_entry)
        
        formatter = JSONFormatter()
    else:
        # Human-readable logging for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, method: str, path: str, 
                status_code: int, duration_ms: float, **extra: Any) -> None:
    """Log an HTTP request."""
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **extra
        }
    )
