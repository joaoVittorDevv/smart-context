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
    'javascript': {
        'module': 'tree_sitter_javascript',
        'extensions': ['.js', '.jsx', '.cjs', '.mjs'],
    },
    'typescript': {
        'module': 'tree_sitter_typescript',
        'extensions': ['.ts', '.tsx'],
    },
    'go': {
        'module': 'tree_sitter_go',
        'extensions': ['.go'],
    },
    'rust': {
        'module': 'tree_sitter_rust',
        'extensions': ['.rs'],
    },
    'java': {
        'module': 'tree_sitter_java',
        'extensions': ['.java'],
    },
    'cpp': {
        'module': 'tree_sitter_cpp',
        'extensions': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
    },
}

# Cache for loaded Grammar objects to avoid re-importing constantly
_LANGUAGE_CACHE: Dict[str, Language] = {}


def detect_language_from_path(file_path: str) -> Optional[str]:
    """Detect language name from file extension based on registry."""
    ext = Path(file_path).suffix.lower()
    for lang_name, config in _LANGUAGE_REGISTRY.items():
        if ext in config['extensions']:
            return lang_name
    return None


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
    if name in _LANGUAGE_CACHE:
        return _LANGUAGE_CACHE[name]

    if name not in _LANGUAGE_REGISTRY:
        raise KeyError(f"Language '{name}' not registered. Available: {list(_LANGUAGE_REGISTRY.keys())}")

    module_name = _LANGUAGE_REGISTRY[name]['module']

    import importlib
    mod = importlib.import_module(module_name)
    
    # typescript module has different signatures for tsx vs ts
    if name == 'typescript':
        lang = Language(mod.language_typescript())
    else:
        lang = Language(mod.language())

    _LANGUAGE_CACHE[name] = lang
    return lang


class TreeSitterParser:
    """
    AST-based code parser using tree-sitter native API.

    Provides precise symbol extraction (classes, functions, methods)
    with correct body boundaries and decorator support.

    Output contract: List[Dict] with keys:
        name, type, file, body, signature, start_line, end_line
    """

    def __init__(self, language: Optional[str] = None):
        """
        Initialize parser. If language is provided, acts as a fixed parser.
        If None, acts as a dynamic parser that detects language from file extension.

        Args:
            language: Programming language name (optional)
        """
        self.default_language = language
        self._parsers: Dict[str, Parser] = {}

    def _get_parser(self, lang_name: str) -> Parser:
        """Get or initialize a parser for a specific language."""
        if lang_name not in self._parsers:
            ts_language = _load_language(lang_name)
            self._parsers[lang_name] = Parser(ts_language)
        return self._parsers[lang_name]

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
            file_path: Optional file path for reference to detect language

        Returns:
            List of symbol dictionaries
        """
        lang_name = self.default_language
        if not lang_name and file_path:
            lang_name = detect_language_from_path(file_path)

        if not lang_name:
            # Fallback or unknown language
            return []

        try:
            parser = self._get_parser(lang_name)
        except (KeyError, ImportError):
            return [] # Silently fail if grammar not available

        if isinstance(source_code, str):
            source_code = source_code.encode('utf-8')

        tree = parser.parse(source_code)
        root = tree.root_node

        symbols: List[Dict] = []

        if lang_name == 'python':
            symbols.extend(self._extract_python_symbols(root, source_code, file_path))
        elif lang_name in ('javascript', 'typescript'):
            symbols.extend(self._extract_js_ts_symbols(root, source_code, file_path))
        elif lang_name == 'go':
            symbols.extend(self._extract_go_symbols(root, source_code, file_path))
        elif lang_name == 'rust':
            symbols.extend(self._extract_rust_symbols(root, source_code, file_path))
        elif lang_name == 'java':
            symbols.extend(self._extract_java_symbols(root, source_code, file_path))
        elif lang_name in ('cpp', 'c'):
            symbols.extend(self._extract_cpp_symbols(root, source_code, file_path))

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
    # ─── JavaScript/TypeScript-specific extraction ───────────────────

    def _extract_js_ts_symbols(
        self, root: Node, source: bytes, file_path: str
    ) -> List[Dict]:
        """Extract classes, interfaces, functions, and methods from JS/TS AST."""
        symbols: List[Dict] = []
        
        # Helper to process a node that could be nested inside export_statement
        def process_node(node: Node):
            # If it's an export block, unwrap it
            if node.type == 'export_statement':
                for child in node.children:
                    process_node(child)
                return

            # Note: typescript uses 'type_identifier' instead of 'name' for types sometimes
            if node.type in ('class_declaration', 'interface_declaration', 'type_alias_declaration'):
                symbols.extend(self._extract_js_ts_class(node, source, file_path))
                
            elif node.type == 'function_declaration':
                symbols.append(
                    self._build_symbol(node, source, file_path, symbol_type='function')
                )
                
            elif node.type == 'lexical_declaration':
                # Catch `const myFunc = () => {}`
                for child in node.children:
                    if child.type == 'variable_declarator':
                        for sub in child.children:
                            if sub.type in ('arrow_function', 'function'):
                                # The symbol is actually the variable declarator holding the name
                                symbols.append(
                                    self._build_symbol(child, source, file_path, symbol_type='function')
                                )

        for child in root.children:
            process_node(child)

        return symbols

    def _extract_js_ts_class(
        self, class_node: Node, source: bytes, file_path: str
    ) -> List[Dict]:
        """Extract a JS/TS class/interface and its methods."""
        symbols: List[Dict] = []

        # Build symbol for the class/interface itself
        symbols.append(
            self._build_symbol(class_node, source, file_path, symbol_type='class')
        )

        body_node = class_node.child_by_field_name('body')
        if body_node is None:
            # Some types like `type X = string;` don't have a body field or are primitive aliases
            return symbols

        for child in body_node.children:
            if child.type == 'method_definition':
                symbols.append(
                    self._build_symbol(child, source, file_path, symbol_type='method')
                )

        return symbols

    # ─── Go-specific extraction ──────────────────────────────────────

    def _extract_go_symbols(
        self, root: Node, source: bytes, file_path: str
    ) -> List[Dict]:
        """Extract classes (structs/interfaces), functions, and methods from Go AST."""
        symbols: List[Dict] = []
        for child in root.children:
            if child.type == 'type_declaration':
                for type_spec in child.children:
                    if type_spec.type == 'type_spec':
                        # We consider any named type declaration as a class (interface, struct, alias)
                        symbols.append(
                            self._build_symbol(type_spec, source, file_path, symbol_type='class')
                        )
            elif child.type == 'function_declaration':
                symbols.append(
                    self._build_symbol(child, source, file_path, symbol_type='function')
                )
            elif child.type == 'method_declaration':
                symbols.append(
                    self._build_symbol(child, source, file_path, symbol_type='method')
                )

        return symbols

    # ─── Rust-specific extraction ────────────────────────────────────

    def _extract_rust_symbols(
        self, root: Node, source: bytes, file_path: str
    ) -> List[Dict]:
        """Extract structs/traits, functions, and impl methods from Rust AST."""
        symbols: List[Dict] = []
        for child in root.children:
            if child.type in ('struct_item', 'trait_item'):
                symbols.append(
                    self._build_symbol(child, source, file_path, symbol_type='class')
                )
            elif child.type == 'function_item':
                symbols.append(
                    self._build_symbol(child, source, file_path, symbol_type='function')
                )
            elif child.type == 'impl_item':
                # An impl doesn't have a name itself, but 'type' field represents its name.
                # All 'function_item's inside its 'declaration_list' are methods.
                decl_list = child.child_by_field_name('body') # No, it is 'declaration_list' usually, wait... let's just search children for declaration_list or block
                decl_list = None
                for c in child.children:
                    if c.type == 'declaration_list':
                        decl_list = c
                        break
                
                if decl_list:
                    for method_node in decl_list.children:
                        if method_node.type == 'function_item':
                            symbols.append(
                                self._build_symbol(method_node, source, file_path, symbol_type='method')
                            )

        return symbols

    # ─── Java-specific extraction ────────────────────────────────────

    def _extract_java_symbols(
        self, root: Node, source: bytes, file_path: str
    ) -> List[Dict]:
        """Extract classes, interfaces, and methods from Java AST."""
        symbols: List[Dict] = []
        
        def process_node(node: Node):
            if node.type in ('class_declaration', 'interface_declaration'):
                symbols.append(
                    self._build_symbol(node, source, file_path, symbol_type='class')
                )
                body = node.child_by_field_name('body')
                if body:
                    for child in body.children:
                        process_node(child)
            elif node.type == 'method_declaration':
                symbols.append(
                    self._build_symbol(node, source, file_path, symbol_type='method')
                )
            else:
                for child in node.children:
                    process_node(child)
                    
        process_node(root)
        return symbols

    # ─── C++-specific extraction ─────────────────────────────────────

    def _extract_cpp_symbols(
        self, root: Node, source: bytes, file_path: str
    ) -> List[Dict]:
        """Extract classes, structs, functions and methods from C/C++ AST."""
        symbols: List[Dict] = []
        
        def process_node(node: Node, in_class=False):
            if node.type in ('class_specifier', 'struct_specifier'):
                symbols.append(
                    self._build_symbol(node, source, file_path, symbol_type='class')
                )
                body = node.child_by_field_name('body')
                if body:
                    for child in body.children:
                        process_node(child, in_class=True)
            elif node.type == 'function_definition':
                symbols.append(
                    self._build_symbol(node, source, file_path, symbol_type=('method' if in_class else 'function'))
                )
            elif node.type == 'field_declaration' and in_class:
                # Methods prototyped in C++ header/class
                for child in node.children:
                    if child.type == 'function_declarator':
                        symbols.append(
                            self._build_symbol(child, source, file_path, symbol_type='method')
                        )
            else:
                for child in node.children:
                    process_node(child, in_class)

        process_node(root)
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
        if name_node is None:
            # JS/TS sometimes put type names under 'name' differently or not at all, let's also check for TS
            if node.type in ('type_alias_declaration', 'interface_declaration', 'class_declaration'):
                name_node = node.child_by_field_name('name') 
                if name_node is None:
                    # In tree-sitter typescript export classes sometimes the identifier is a child with type 'type_identifier'
                    for c in node.children:
                        if c.type == 'type_identifier' or c.type == 'identifier':
                            name_node = c
                            break
            # Go method_declaration puts name under field_identifier
            elif node.type == 'method_declaration':
                name_node = node.child_by_field_name('name')
            # Rust impl_item target name isn't on the impl_item but we only pass function_item which has 'name'.

        if name_node is None:
            # Universal fallback: use the first 'identifier' or 'type_identifier' or 'field_identifier' child
            def find_identifier(n):
                for c in n.children:
                    if c.type in ('identifier', 'type_identifier', 'field_identifier', 'property_identifier'):
                        return c
                    if c.type == 'function_declarator':
                        return find_identifier(c)
                return None
            name_node = find_identifier(node)

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
