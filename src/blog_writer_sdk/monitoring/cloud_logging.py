"""
Google Cloud Logging integration for BlogWriter SDK.

Provides structured logging that integrates seamlessly with Google Cloud Logging
and Cloud Run's built-in logging capabilities.
"""

import os
import json
import logging
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime
from contextlib import contextmanager
import time

# Try to import Google Cloud Logging, fall back to standard logging if not available
try:
    from google.cloud import logging as cloud_logging
    from google.cloud.logging.handlers import CloudLoggingHandler
    GOOGLE_CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_LOGGING_AVAILABLE = False
    cloud_logging = None
    CloudLoggingHandler = None

from .metrics import get_metrics_collector


class CloudLoggingFormatter(logging.Formatter):
    """Custom formatter for Google Cloud Logging compatibility."""
    
    def format(self, record):
        """Format log record for Google Cloud Logging."""
        # Base log entry
        log_entry = {
            'timestamp': datetime.now().astimezone().isoformat(),
            'severity': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class BlogWriterLogger:
    """
    Enhanced logger for BlogWriter SDK with Google Cloud Logging integration.
    
    Provides structured logging with:
    - Request correlation IDs
    - Performance metrics
    - Business context
    - Error tracking
    - Google Cloud Logging compatibility
    """
    
    def __init__(self, name: str = "blog_writer", use_cloud_logging: bool = True):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            use_cloud_logging: Whether to use Google Cloud Logging
        """
        self.logger = logging.getLogger(name)
        self.use_cloud_logging = use_cloud_logging and GOOGLE_CLOUD_LOGGING_AVAILABLE
        self._setup_logger()
        
        # Request context storage
        self._request_context = {}
    
    def _setup_logger(self):
        """Set up the logger with appropriate handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level from environment
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        if self.use_cloud_logging:
            self._setup_cloud_logging()
        else:
            self._setup_standard_logging()
    
    def _setup_cloud_logging(self):
        """Set up Google Cloud Logging handler."""
        try:
            # Initialize Cloud Logging client
            client = cloud_logging.Client()
            
            # Create Cloud Logging handler
            handler = CloudLoggingHandler(client)
            handler.setLevel(logging.INFO)
            
            # Use JSON formatter for structured logging
            formatter = CloudLoggingFormatter()
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
            self.logger.info("Google Cloud Logging initialized successfully")
            
        except Exception as e:
            # Fall back to standard logging if Cloud Logging fails
            self.logger.warning(f"Failed to initialize Google Cloud Logging: {e}")
            self._setup_standard_logging()
    
    def _setup_standard_logging(self):
        """Set up standard console logging."""
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # Use JSON formatter for structured logging
        formatter = CloudLoggingFormatter()
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    @contextmanager
    def request_context(self, request_id: str, **context):
        """
        Context manager for request-scoped logging.
        
        Args:
            request_id: Unique request identifier
            **context: Additional context data
        """
        old_context = self._request_context.copy()
        self._request_context.update({
            'request_id': request_id,
            'timestamp': time.time(),
            **context
        })
        
        try:
            yield self
        finally:
            self._request_context = old_context
    
    def _get_log_data(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Get structured log data with context."""
        log_data = {
            'level': level,
            'message': message,
            'timestamp': datetime.now().astimezone().isoformat(),
            **self._request_context,
            **kwargs
        }
        
        # Add metrics if available
        metrics_collector = get_metrics_collector()
        if metrics_collector:
            log_data['metrics'] = {
                'uptime_seconds': time.time() - getattr(metrics_collector, '_start_time', time.time()),
                'request_count': sum(metrics_collector.counters.get(k, 0) 
                                   for k in metrics_collector.counters 
                                   if 'http_requests_total' in k)
            }
        
        return log_data
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        log_data = self._get_log_data('INFO', message, **kwargs)
        self.logger.info(json.dumps(log_data, default=str))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        log_data = self._get_log_data('WARNING', message, **kwargs)
        self.logger.warning(json.dumps(log_data, default=str))
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with context and exception details."""
        log_data = self._get_log_data('ERROR', message, **kwargs)
        
        if exception:
            log_data['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        self.logger.error(json.dumps(log_data, default=str))
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        log_data = self._get_log_data('DEBUG', message, **kwargs)
        self.logger.debug(json.dumps(log_data, default=str))
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        log_data = self._get_log_data('CRITICAL', message, **kwargs)
        self.logger.critical(json.dumps(log_data, default=str))
    
    def log_blog_generation(self, topic: str, success: bool, word_count: int, 
                          generation_time: float, **kwargs):
        """Log blog generation event with business context."""
        self.info(
            f"Blog generation {'completed' if success else 'failed'}",
            event_type='blog_generation',
            topic=topic,
            success=success,
            word_count=word_count,
            generation_time_seconds=generation_time,
            **kwargs
        )
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       duration: float, **kwargs):
        """Log API request with performance metrics."""
        level = 'WARNING' if status_code >= 400 else 'INFO'
        getattr(self, level.lower())(
            f"API request {method} {endpoint}",
            event_type='api_request',
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_seconds=duration,
            **kwargs
        )
    
    def log_performance(self, operation: str, duration: float, success: bool, **kwargs):
        """Log performance metrics."""
        level = 'WARNING' if not success else 'INFO'
        getattr(self, level.lower())(
            f"Performance: {operation}",
            event_type='performance',
            operation=operation,
            duration_seconds=duration,
            success=success,
            **kwargs
        )
    
    def log_system_health(self, health_data: Dict[str, Any]):
        """Log system health status."""
        status = health_data.get('status', 'unknown')
        level = 'ERROR' if status == 'unhealthy' else 'WARNING' if status == 'degraded' else 'INFO'
        
        getattr(self, level.lower())(
            f"System health: {status}",
            event_type='system_health',
            **health_data
        )


# Global logger instance
_blog_logger: Optional[BlogWriterLogger] = None


def initialize_cloud_logging(name: str = "blog_writer", use_cloud_logging: bool = True) -> BlogWriterLogger:
    """Initialize the global cloud logger."""
    global _blog_logger
    _blog_logger = BlogWriterLogger(name=name, use_cloud_logging=use_cloud_logging)
    return _blog_logger


def get_blog_logger() -> BlogWriterLogger:
    """Get the global blog logger instance."""
    global _blog_logger
    if _blog_logger is None:
        _blog_logger = BlogWriterLogger()
    return _blog_logger


# Convenience functions for common logging operations
def log_blog_generation(topic: str, success: bool, word_count: int, generation_time: float, **kwargs):
    """Log blog generation event."""
    get_blog_logger().log_blog_generation(topic, success, word_count, generation_time, **kwargs)


def log_api_request(method: str, endpoint: str, status_code: int, duration: float, **kwargs):
    """Log API request."""
    get_blog_logger().log_api_request(method, endpoint, status_code, duration, **kwargs)


def log_performance(operation: str, duration: float, success: bool, **kwargs):
    """Log performance metrics."""
    get_blog_logger().log_performance(operation, duration, success, **kwargs)


def log_system_health(health_data: Dict[str, Any]):
    """Log system health."""
    get_blog_logger().log_system_health(health_data)
