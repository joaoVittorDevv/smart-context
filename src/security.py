"""
Security utilities for MCP Context Server.

This module provides input validation and security checks.
"""

import re
import os
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Validates inputs and performs security checks.
    """

    # Patterns for detecting potential attacks
    SQL_INJECTION_PATTERNS = [
        r"(?i)(\b(ALTER|CREATE|DELETE|DROP|EXECUTE|INSERT|SELECT|UNION|UPDATE)\b)",
        r"(?i)(--|;|\/\*|\*\/)",
        r"(?i)(\bOR\b.*=.*=)",
        r"(?i)(\bAND\b.*=.*=)"
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r'\.\.[\\/]',
        r'\.\.%2f',
        r'%2e%2e',
        r'%252e%252e',
        r'\.\.%5c',
        r'%2e%5c'
    ]

    COMMAND_INJECTION_PATTERNS = [
        r'[;&|`$()]',
        r'\$\(.*\)',
        r'`.*`',
        r'\|.*\|'
    ]

    @staticmethod
    def validate_path(file_path: str, project_root: str) -> bool:
        """
        Validate that a file path is within the project root (Path Traversal protection).

        Args:
            file_path: File path to validate
            project_root: Root directory of the project

        Returns:
            True if path is valid, False otherwise
        """
        try:
            # Convert to absolute paths
            file_abs = Path(file_path).resolve()
            root_abs = Path(project_root).resolve()

            # Check if file is within project root
            try:
                file_abs.relative_to(root_abs)
                return True
            except ValueError:
                logger.warning(f"Path traversal attempt detected: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error validating path '{file_path}': {e}")
            return False

    @staticmethod
    def validate_symbol_name(symbol_name: str) -> bool:
        """
        Validate symbol name for safety.

        Args:
            symbol_name: Symbol name to validate

        Returns:
            True if valid, False otherwise
        """
        if not symbol_name:
            return False

        # Check length
        if len(symbol_name) > 200:
            return False

        # Check for valid characters (alphanumeric, underscore, dot)
        # Allow module notation (e.g., "module.Class")
        pattern = r'^[A-Za-z_][A-Za-z0-9_\.]*$'
        if not re.match(pattern, symbol_name):
            return False

        return True

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 10000) -> str:
        """
        Sanitize string input by removing dangerous characters.

        Args:
            input_str: Input string
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not input_str:
            return ""

        # Truncate to max length
        if len(input_str) > max_length:
            input_str = input_str[:max_length]

        # Remove null bytes
        input_str = input_str.replace('\x00', '')

        # Remove control characters except newline and tab
        cleaned = ''.join(
            c for c in input_str
            if c.isprintable() or c in '\n\t'
        )

        return cleaned

    @staticmethod
    def validate_category(category: Optional[str]) -> bool:
        """
        Validate observation category.

        Args:
            category: Category to validate

        Returns:
            True if valid, False otherwise
        """
        if not category:
            return True  # Category is optional

        valid_categories = ['bug', 'refactor', 'logic', 'architecture']
        return category in valid_categories

    @staticmethod
    def validate_priority(priority: int) -> bool:
        """
        Validate observation priority.

        Args:
            priority: Priority to validate

        Returns:
            True if valid, False otherwise
        """
        return isinstance(priority, int) and 1 <= priority <= 5

    @staticmethod
    def detect_sql_injection(input_str: str) -> bool:
        """
        Detect potential SQL injection in input.

        Args:
            input_str: Input string to check

        Returns:
            True if SQL injection detected, False otherwise
        """
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {input_str[:100]}")
                return True
        return False

    @staticmethod
    def detect_path_traversal(file_path: str) -> bool:
        """
        Detect potential path traversal in input.

        Args:
            file_path: File path to check

        Returns:
            True if path traversal detected, False otherwise
        """
        for pattern in SecurityValidator.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                logger.warning(f"Potential path traversal detected: {file_path}")
                return True
        return False

    @classmethod
    def validate_tool_arguments(cls, tool_name: str, arguments: dict) -> tuple[bool, Optional[str]]:
        """
        Validate arguments for a tool call.

        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments

        Returns:
            Tuple of (is_valid, error_message)
        """
        if tool_name == "get_symbol_context":
            symbol_name = arguments.get('symbol_name', '')

            if not symbol_name:
                return False, "symbol_name is required"

            if not cls.validate_symbol_name(symbol_name):
                return False, f"Invalid symbol name: {symbol_name}"

            if cls.detect_sql_injection(symbol_name):
                return False, "Invalid characters in symbol_name"

        elif tool_name == "add_observation":
            symbol_name = arguments.get('symbol_name', '')
            content = arguments.get('content', '')
            category = arguments.get('category')
            priority = arguments.get('priority', 3)

            if not symbol_name:
                return False, "symbol_name is required"

            if not content:
                return False, "content is required"

            if not cls.validate_symbol_name(symbol_name):
                return False, f"Invalid symbol name: {symbol_name}"

            content_clean = cls.sanitize_string(content, max_length=5000)
            if content != content_clean:
                logger.warning("Content was sanitized due to invalid characters")
                # Could optionally warn user about sanitization

            if not cls.validate_category(category):
                return False, f"Invalid category: {category}. Must be one of: bug, refactor, logic, architecture"

            if not cls.validate_priority(priority):
                return False, "Priority must be between 1 and 5"

        elif tool_name == "get_project_summary":
            # No arguments to validate
            pass

        return True, None


__all__ = ['SecurityValidator']
