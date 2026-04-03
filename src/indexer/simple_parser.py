"""
Simple regex-based code parser (fallback for MVP).

This module provides basic code parsing using regex patterns.
Works for Python initially, can be extended for other languages.
"""

import re
from typing import List, Dict, Optional
from pathlib import Path


class SimpleCodeParser:
    """
    Simple regex-based code parser for MVP.

    Provides basic symbol extraction without tree-sitter dependency.
    """

    def __init__(self, language: str = 'python'):
        """
        Initialize parser for a specific language.

        Args:
            language: Programming language (default: 'python')
        """
        self.language = language

        if language == 'python':
            self._setup_python_patterns()
        else:
            print(f"Warning: Language '{language}' not yet supported")
            self.patterns = {}

    def _setup_python_patterns(self):
        """Setup regex patterns for Python."""
        self.patterns = {
            # Pattern for class definitions
            'class': re.compile(
                r'^class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?:',
                re.MULTILINE
            ),
            # Pattern for function/method definitions
            'function': re.compile(
                r'^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(',
                re.MULTILINE
            ),
            # Pattern for imports
            'import': re.compile(
                r'^(?:from\s+(\S+)\s+)?import\s+(.+)',
                re.MULTILINE
            )
        }

    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Parse a file and extract symbols.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of symbol dictionaries
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        return self.parse_code(source_code, str(file_path))

    def parse_code(self, source_code: str, file_path: str = '') -> List[Dict]:
        """
        Parse source code and extract symbols.

        Args:
            source_code: Source code as string
            file_path: Optional file path for reference

        Returns:
            List of symbol dictionaries
        """
        if self.language != 'python':
            print(f"Warning: Parsing for '{self.language}' not implemented")
            return []

        symbols = []
        lines = source_code.split('\n')

        # Find classes
        for match in self.patterns['class'].finditer(source_code):
            name = match.group(1)
            start_pos = match.start()
            start_line = source_code[:start_pos].count('\n') + 1

            # Extract class body (simplified - until next class/function or end)
            body = self._extract_body(source_code, match.end(), start_line)

            symbols.append({
                'name': name,
                'type': 'class',
                'file': file_path,
                'body': body,
                'signature': match.group(0),
                'start_line': start_line,
                'end_line': start_line + body.count('\n') + 1
            })

        # Find functions (excluding methods inside classes for now)
        in_class = False
        class_indent = 0

        for i, line in enumerate(lines):
            # Track class indentation
            if line.strip().startswith('class '):
                in_class = True
                class_indent = len(line) - len(line.lstrip())
            elif in_class and line.strip() and not line.startswith(' ' * (class_indent + 1)):
                in_class = False

            # Skip methods inside classes
            if in_class:
                continue

            match = self.patterns['function'].match(line)
            if match:
                name = match.group(1)
                start_line = i + 1

                # Extract function body
                body_start = match.end()
                body = self._extract_body(source_code, body_start, start_line)

                symbols.append({
                    'name': name,
                    'type': 'function',
                    'file': file_path,
                    'body': body,
                    'signature': line.strip(),
                    'start_line': start_line,
                    'end_line': start_line + body.count('\n') + 1
                })

        return symbols

    def _extract_body(self, source_code: str, start_pos: int, start_line: int) -> str:
        """
        Extract the body of a class or function.

        Args:
            source_code: Full source code
            start_pos: Position where body starts
            start_line: Line number where body starts

        Returns:
            Body as string
        """
        # Find the next line at same or lower indentation
        lines = source_code[start_pos:].split('\n')
        body_lines = []
        base_indent = None

        for line in lines:
            if not body_lines:
                # First line after definition
                if line.strip() == '':
                    continue
                if line.strip().startswith(':'):
                    continue
                base_indent = len(line) - len(line.lstrip())
                if base_indent == 0:
                    # No indentation, must be inline
                    body_lines.append(line)
                    break

            # Check if we've exited the block
            if line.strip() and not line.startswith(' '):
                break

            body_lines.append(line)

        return '\n'.join(body_lines)


# Use tree-sitter native parser when available, fallback to regex
try:
    from .ts_parser import TreeSitterParser as CodeParser
except ImportError:
    CodeParser = SimpleCodeParser
