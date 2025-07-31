"""
Safe output management for preventing Claude Code overflow issues.

This module provides utilities to manage console output and prevent
Claude Code "Invalid string length" errors by implementing output
truncation, safe printing functions, and monitoring capabilities.
"""

import logging
from typing import Any


class SafeOutputManager:
    """
    Manager for safe output handling to prevent Claude Code overflow.
    
    Implements the multi-layered approach from the overflow solution:
    - Output size tracking and limiting
    - Safe printing functions
    - Truncation with user notification
    - Emergency output controls
    """

    def __init__(self, max_console_output: int = 100000):  # 100KB default limit
        """Initialize the safe output manager."""
        self.max_console_output = max_console_output
        self.total_output_size = 0
        self.truncated = False
        self.truncation_warned = False

        # Configure logging with reduced verbosity
        self._setup_safe_logging()

    def _setup_safe_logging(self) -> None:
        """Configure logging to prevent excessive output."""
        # Set warning level to reduce verbosity
        logging.getLogger().setLevel(logging.WARNING)

        # Configure specific loggers (safely handle missing modules)
        try:
            logging.getLogger("llama_index").setLevel(logging.WARNING)
        except:
            pass
        try:
            logging.getLogger("httpx").setLevel(logging.WARNING)
        except:
            pass
        try:
            logging.getLogger("openai").setLevel(logging.WARNING)
        except:
            pass

    def safe_print(self, *args, **kwargs) -> bool:
        """
        Print with output size checking to prevent overflow.
        
        Args:
            *args: Arguments to print
            **kwargs: Keyword arguments for print
            
        Returns:
            bool: True if printed successfully, False if truncated
        """
        # Convert all arguments to string and calculate size
        str_message = " ".join(str(arg) for arg in args)
        message_size = len(str_message.encode("utf-8"))

        # Check if adding this message would exceed limit
        if self.total_output_size + message_size > self.max_console_output:
            if not self.truncation_warned:
                print(f"\n[OUTPUT TRUNCATED: Exceeded {self.max_console_output} bytes to prevent Claude Code overflow]")
                self.truncation_warned = True
                self.truncated = True
            return False

        # Safe to print with Unicode error handling
        try:
            print(str_message, **kwargs)
        except UnicodeEncodeError:
            # Fallback: Replace problematic Unicode characters
            safe_message = str_message.encode('ascii', errors='replace').decode('ascii')
            print(safe_message, **kwargs)
        self.total_output_size += message_size
        return True

    def truncate_string(self, text: str, max_length: int = 10000, suffix: str = "... [TRUNCATED]") -> str:
        """
        Safely truncate a string to prevent memory issues.
        
        Args:
            text: String to truncate
            max_length: Maximum allowed length
            suffix: Suffix to add when truncating
            
        Returns:
            str: Truncated string or original if under limit
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    def safe_format_response(self, result: Any, max_length: int = 5000) -> str:
        """
        Safely format a response object for display.
        
        Args:
            result: Result object to format
            max_length: Maximum length for formatted output
            
        Returns:
            str: Safely formatted response
        """
        try:
            if isinstance(result, dict):
                # Format dictionary with key truncation
                formatted = {}
                for key, value in result.items():
                    str_value = str(value)
                    if len(str_value) > 500:  # Truncate long values
                        str_value = str_value[:500] + "... [TRUNCATED]"
                    formatted[key] = str_value

                result_str = str(formatted)
            else:
                result_str = str(result)

            return self.truncate_string(result_str, max_length)

        except (MemoryError, OverflowError):
            return "[LARGE OUTPUT ERROR: Result too large for safe handling]"

    def get_output_stats(self) -> dict[str, Any]:
        """
        Get current output statistics.
        
        Returns:
            Dict with output statistics
        """
        return {
            "total_output_size": self.total_output_size,
            "max_console_output": self.max_console_output,
            "remaining_capacity": max(0, self.max_console_output - self.total_output_size),
            "truncated": self.truncated,
            "truncation_warned": self.truncation_warned,
            "usage_percentage": (self.total_output_size / self.max_console_output) * 100
        }

    def reset_output_tracking(self) -> None:
        """Reset output tracking counters."""
        self.total_output_size = 0
        self.truncated = False
        self.truncation_warned = False


# Global output manager instance
_output_manager_instance: SafeOutputManager | None = None


def get_output_manager() -> SafeOutputManager:
    """Get the global safe output manager instance."""
    global _output_manager_instance
    if _output_manager_instance is None:
        _output_manager_instance = SafeOutputManager()
    return _output_manager_instance


def safe_print(*args, **kwargs) -> bool:
    """Convenience function for safe printing."""
    return get_output_manager().safe_print(*args, **kwargs)


def truncate_string(text: str, max_length: int = 10000) -> str:
    """Convenience function for string truncation."""
    return get_output_manager().truncate_string(text, max_length)


def safe_format_response(result: Any, max_length: int = 5000) -> str:
    """Convenience function for safe response formatting."""
    return get_output_manager().safe_format_response(result, max_length)


class TruncatedStreamHandler(logging.StreamHandler):
    """Stream handler that truncates output to prevent memory issues."""

    def __init__(self, stream=None, max_output_size: int = 100000):
        super().__init__(stream)
        self.max_output_size = max_output_size
        self.current_output_size = 0
        self.truncation_warned = False

    def emit(self, record):
        """Emit a record with output size checking."""
        try:
            msg = self.format(record)
            msg_size = len(msg.encode("utf-8"))

            if self.current_output_size + msg_size > self.max_output_size:
                if not self.truncation_warned:
                    truncation_msg = f"\n[LOG OUTPUT TRUNCATED: Exceeded {self.max_output_size} bytes]\n"
                    super().emit(logging.LogRecord(
                        name="output_manager",
                        level=logging.WARNING,
                        pathname="",
                        lineno=0,
                        msg=truncation_msg,
                        args=(),
                        exc_info=None
                    ))
                    self.truncation_warned = True
                return

            self.current_output_size += msg_size
            super().emit(record)

        except Exception:
            # Fail silently to prevent recursive errors
            pass


def handle_large_output_error(func):
    """Decorator to handle functions that might produce large output."""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return safe_format_response(result)
        except (MemoryError, OverflowError) as e:
            return f"[LARGE OUTPUT ERROR: {type(e).__name__} - Output too large for safe handling]"
    return wrapper
