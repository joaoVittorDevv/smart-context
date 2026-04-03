"""
Tree-sitter native code parser.

Uses tree-sitter >= 0.25 with dedicated grammar packages (tree-sitter-python)
for precise AST-based symbol extraction. Replaces the regex fallback (simple_parser.py).

Decision #011: Migration from regex to tree-sitter native parser.
"""

from typing import List, Dict, Optional
from pathlib import Path

from tree_sitter import Language, Parser, Node


# Language registry: maps language name -> (module, extensions)
_LANGUAGE_REGISTRY = {
    'python': {
        'module': 'tree_sitter_python',
        'extensions': ['.py'],
    },
    # Future: add 'javascript', 'typescript', 'go', 'rust' here
}


def _load_language(name: str) -> Language:
    """
    Dynamically load a tree-sitter language grammar.

    Args:
        name: Language name (e.g. 'python')

    Returns:
        Language object

    Raises:
        ImportError: If the grammar package is not installed
        KeyError: If the language is not registered
    """
    if name not in _LANGUAGE_REGISTRY:
        raise KeyError(f"Language '{name}' not registered. Available: {list(_LANGUAGE_REGISTRY.keys())}")

    module_name = _LANGUAGE_REGISTRY[name]['module']

    import importlib
    mod = importlib.import_module(module_name)
    return Language(mod.language())


class TreeSitterParser:
    """
    AST-based code parser using tree-sitter native API.

    Provides precise symbol extraction (classes, functions, methods)
    with correct body boundaries and decorator support.

    Output contract: List[Dict] with keys:
        name, type, file, body, signature, start_line, end_line
    """

    def __init__(self, language: str = 'python'):
        """
        Initialize parser for a specific language.

        Args:
            language: Programming language (default: 'python')
        """
        self.language_name = language
        self._ts_language = _load_language(language)
        self._parser = Parser(self._ts_language)

    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Parse a file and extract symbols.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of symbol dictionaries
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        source = path.read_bytes()
        return self.parse_code(source, str(file_path))

    def parse_code(self, source_code: bytes, file_path: str = '') -> List[Dict]:
        """
        Parse source code bytes and extract symbols.

        Args:
            source_code: Source code as bytes (UTF-8)
            file_path: Optional file path for reference

        Returns:
            List of symbol dictionaries
        """
        if isinstance(source_code, str):
            source_code = source_code.encode('utf-8')

        tree = self._parser.parse(source_code)
        root = tree.root_node

        symbols: List[Dict] = []

        if self.language_name == 'python':
            symbols.extend(self._extract_python_symbols(root, source_code, file_path))

        return symbols

    # ─── Python-specific extraction ──────────────────────────────────

    def _extract_python_symbols(
        self, root: Node, source: bytes, file_path: str
    ) -> List[Dict]:
        """Extract classes, functions, and methods from Python AST."""
        symbols: List[Dict] = []

        for child in root.children:
            if child.type == 'class_definition':
                symbols.extend(
                    self._extract_class(child, source, file_path)
                )

            elif child.type == 'function_definition':
                symbols.append(
                    self._build_symbol(child, source, file_path, symbol_type='function')
                )

            elif child.type == 'decorated_definition':
                inner = self._get_decorated_inner(child)
                if inner is not None:
                    if inner.type == 'class_definition':
                        symbols.extend(
                            self._extract_class(inner, source, file_path, decorator_node=child)
                        )
                    elif inner.type == 'function_definition':
                        symbols.append(
                            self._build_symbol(
                                inner, source, file_path,
                                symbol_type='function',
                                decorator_node=child,
                            )
                        )

        return symbols

    def _extract_class(
        self,
        class_node: Node,
        source: bytes,
        file_path: str,
        decorator_node: Optional[Node] = None,
    ) -> List[Dict]:
        """
        Extract a class and its methods.

        Returns a list: [class_symbol, method1, method2, ...]
        """
        symbols: List[Dict] = []

        # The class itself
        symbols.append(
            self._build_symbol(
                class_node, source, file_path,
                symbol_type='class',
                decorator_node=decorator_node,
            )
        )

        # Methods inside the class body
        body_node = class_node.child_by_field_name('body')
        if body_node is None:
            return symbols

        for child in body_node.children:
            if child.type == 'function_definition':
                symbols.append(
                    self._build_symbol(child, source, file_path, symbol_type='method')
                )

            elif child.type == 'decorated_definition':
                inner = self._get_decorated_inner(child)
                if inner is not None and inner.type == 'function_definition':
                    symbols.append(
                        self._build_symbol(
                            inner, source, file_path,
                            symbol_type='method',
                            decorator_node=child,
                        )
                    )

        return symbols

    # ─── Helper methods ──────────────────────────────────────────────

    def _build_symbol(
        self,
        node: Node,
        source: bytes,
        file_path: str,
        symbol_type: str,
        decorator_node: Optional[Node] = None,
    ) -> Dict:
        """
        Build a symbol dictionary from a tree-sitter node.

        Matches the output contract consumed by IncrementalIndexer,
        DependencyAnalyzer, and SymbolRepository.
        """
        name_node = node.child_by_field_name('name')
        name = name_node.text.decode('utf-8') if name_node else '<anonymous>'

        body_node = node.child_by_field_name('body')
        body = body_node.text.decode('utf-8') if body_node else ''

        signature = self._get_signature(node, source)

        # If there's a decorator, the definition starts at the decorator
        outer = decorator_node if decorator_node else node
        start_line = outer.start_point[0] + 1  # 1-indexed
        end_line = outer.end_point[0] + 1

        return {
            'name': name,
            'type': symbol_type,
            'file': file_path,
            'body': body,
            'signature': signature,
            'start_line': start_line,
            'end_line': end_line,
        }

    @staticmethod
    def _get_signature(node: Node, source: bytes) -> str:
        """
        Extract the first line of a definition as its signature.

        Examples:
            'class MyClass(Base):'
            'def my_func(self, arg):'
            'async def fetch_data(url: str) -> dict:'
        """
        start = node.start_byte
        # Find end of first line
        nl_pos = source.find(b'\n', start)
        if nl_pos == -1:
            nl_pos = len(source)
        sig = source[start:nl_pos].decode('utf-8').strip()
        return sig[:200]  # Limit length

    @staticmethod
    def _get_decorated_inner(decorated_node: Node) -> Optional[Node]:
        """
        Get the inner definition from a decorated_definition node.

        A decorated_definition contains decorator(s) + the actual
        class_definition or function_definition.
        """
        for child in decorated_node.children:
            if child.type in ('class_definition', 'function_definition'):
                return child
        return None
