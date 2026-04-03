"""
Tree-sitter based code parser.

This module provides a generic parser using tree-sitter for multiple languages.
"""

from tree_sitter import Node
from typing import List, Dict, Optional
from pathlib import Path


class CodeParser:
    """
    Generic code parser using tree-sitter.

    Supports multiple programming languages through tree-sitter grammars.
    """

    # Tree-sitter queries for different symbol types
    LANGUAGE_QUERIES = {
        'python': {
            'classes': '''
                (class_definition
                    name: (identifier) @name
                    body: (block) @body) @class_def
            ''',
            'functions': '''
                (function_definition
                    name: (identifier) @name
                    parameters: (parameters) @params
                    body: (block) @body) @func_def
            ''',
            'methods': '''
                (class_definition
                    body: (block
                        (function_definition
                            name: (identifier) @name
                            body: (block) @body) @method_def))
            ''',
            'imports': '''
                (import_statement
                    name: (dotted_name | aliased_import) @name) @import_stmt
                (import_from_statement
                    module_name: (dotted_name) @module
                    name: (dotted_name | aliased_import) @name) @from_import
            ''',
            'calls': '''
                (call
                    function: (identifier) @func) @call
            '''
        }
    }

    def __init__(self, language: str = 'python'):
        """
        Initialize parser for a specific language.

        Args:
            language: Programming language (default: 'python')
        """
        self.language = language

        # Use tree-sitter-languages to get parser
        try:
            import tree_sitter_languages as tsl
            self.parser = tsl.get_parser(language)
        except Exception as e:
            print(f"Warning: Could not load parser for '{language}': {e}")
            self.parser = None

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

        with open(file_path, 'rb') as f:
            source_code = f.read()

        return self.parse_code(source_code, str(file_path))

    def parse_code(self, source_code: bytes, file_path: str = '') -> List[Dict]:
        """
        Parse source code and extract symbols.

        Args:
            source_code: Source code as bytes
            file_path: Optional file path for reference

        Returns:
            List of symbol dictionaries
        """
        tree = self.parser.parse(source_code)
        symbols = []

        # Get queries for the language
        queries = self.LANGUAGE_QUERIES.get(self.language, {})

        # Extract each type of symbol
        for symbol_type, query_str in queries.items():
            try:
                query = self.language_tree_query(query_str)
                captures = query.captures(tree.root_node)

                for capture_node, capture_name in captures:
                    symbol = self._extract_symbol_info(
                        capture_node,
                        capture_name,
                        source_code,
                        file_path
                    )
                    if symbol:
                        symbols.append(symbol)
            except Exception as e:
                # Log warning but continue parsing other symbol types
                print(f"Warning: Failed to parse {symbol_type}: {e}")

        return symbols

    def language_tree_query(self, query_str: str):
        """Create a tree-sitter query for the current language."""
        import re
        from tree_sitter import Query

        # Clean up the query string (remove extra whitespace)
        query_str = re.sub(r'\s+', ' ', query_str).strip()

        return Query(self.parser.language, query_str)

    def _extract_symbol_info(
        self,
        node: Node,
        capture_name: str,
        source_code: bytes,
        file_path: str
    ) -> Optional[Dict]:
        """
        Extract symbol information from a tree-sitter node.

        Args:
            node: Tree-sitter node
            capture_name: Name of the capture
            source_code: Original source code
            file_path: File path for reference

        Returns:
            Symbol dictionary or None
        """
        try:
            # Get symbol name from the node
            name_node = None
            if node.type == 'identifier':
                name_node = node
            else:
                # Try to find identifier child
                for child in node.children:
                    if child.type == 'identifier':
                        name_node = child
                        break

            if not name_node:
                return None

            name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')

            # Get body/definition if available
            body = ''
            if 'body' in capture_name or capture_name in ['class_def', 'func_def', 'method_def']:
                # Find the block/body node
                for child in node.children:
                    if child.type == 'block':
                        body = source_code[child.start_byte:child.end_byte].decode('utf-8')
                        break

            return {
                'name': name,
                'type': self._get_symbol_type(capture_name),
                'file': file_path,
                'body': body,
                'signature': self._get_signature(node, source_code),
                'start_line': node.start_point[0] + 1,
                'end_line': node.end_point[0] + 1
            }
        except Exception as e:
            print(f"Warning: Failed to extract symbol info: {e}")
            return None

    def _get_symbol_type(self, capture_name: str) -> str:
        """Map capture name to symbol type."""
        capture_lower = capture_name.lower()
        if 'class' in capture_lower:
            return 'class'
        elif 'method' in capture_lower:
            return 'method'
        elif 'func' in capture_lower:
            return 'function'
        else:
            return 'unknown'

    def _get_signature(self, node: Node, source_code: bytes) -> str:
        """Extract function/class signature."""
        try:
            # Get the line containing the definition
            start_byte = node.start_byte
            end_byte = start_byte

            # Find end of line
            while end_byte < len(source_code) and source_code[end_byte] not in [b'\n', b'\r'][0]:
                end_byte += 1

            signature = source_code[start_byte:end_byte].decode('utf-8').strip()
            return signature[:200]  # Limit signature length
        except Exception:
            return ''
