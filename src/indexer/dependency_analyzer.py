"""
Dependency analyzer for code symbols.

This module analyzes code to identify dependencies between symbols.
"""

import re
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass


@dataclass
class Dependency:
    """Represents a dependency relationship."""
    caller_name: str
    callee_name: str
    call_site_line: int


class DependencyAnalyzer:
    """
    Analyzes dependencies between code symbols.

    Identifies function calls and references between symbols.
    """

    # Built-in Python symbols to ignore
    BUILTIN_IGNORE = {
        'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
        'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
        'open', 'input', 'isinstance', 'issubclass', 'hasattr', 'getattr',
        'setattr', 'delattr', 'type', 'super', 'self', 'cls'
    }

    def __init__(self):
        """Initialize dependency analyzer."""
        self.symbol_map: Dict[str, Dict] = {}

    def analyze(self, symbols: List[Dict]) -> List[Dict]:
        """
        Analyze dependencies between symbols.

        Args:
            symbols: List of symbol dictionaries from parser

        Returns:
            List of dependency dictionaries ready for database insertion
        """
        # Build symbol lookup map
        self.symbol_map = {s['name']: s for s in symbols}

        dependencies = []

        for caller in symbols:
            calls = self._extract_calls(caller)
            for call_name, line in calls:
                if call_name in self.symbol_map and call_name != caller['name']:
                    callee = self.symbol_map[call_name]
                    dependencies.append({
                        'caller_id': caller.get('id', ''),
                        'callee_id': callee.get('id', ''),
                        'call_site_line': line
                    })

        return dependencies

    def _extract_calls(self, symbol: Dict) -> List[Tuple[str, int]]:
        """
        Extract function calls from a symbol's body.

        Args:
            symbol: Symbol dictionary

        Returns:
            List of (called_function_name, line_number) tuples
        """
        body = symbol.get('body', '')
        if not body:
            return []

        calls = []
        lines = body.split('\n')

        # Pattern to match function calls: identifier(
        call_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')

        for line_num, line in enumerate(lines, start=symbol.get('start_line', 1)):
            # Skip comment lines
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            # Find all function calls in the line
            for match in call_pattern.finditer(line):
                func_name = match.group(1)

                # Skip built-ins and common keywords
                if func_name in self.BUILTIN_IGNORE:
                    continue

                # Skip keywords
                if func_name in ['if', 'for', 'while', 'with', 'try', 'except', 'finally', 'class', 'def', 'return', 'yield', 'raise', 'import', 'from']:
                    continue

                calls.append((func_name, line_num))

        return calls

    def find_callers(self, symbol_name: str, symbols: List[Dict]) -> List[str]:
        """
        Find all symbols that call the given symbol.

        Args:
            symbol_name: Name of the symbol to find callers for
            symbols: List of all symbols

        Returns:
            List of caller symbol names
        """
        callers = []

        for symbol in symbols:
            calls = self._extract_calls(symbol)
            for call_name, _ in calls:
                if call_name == symbol_name:
                    callers.append(symbol['name'])
                    break

        return callers

    def find_callees(self, symbol_name: str, symbols: List[Dict]) -> List[str]:
        """
        Find all symbols called by the given symbol.

        Args:
            symbol_name: Name of the symbol to find callees for
            symbols: List of all symbols

        Returns:
            List of callee symbol names
        """
        # Find the symbol
        symbol = next((s for s in symbols if s['name'] == symbol_name), None)
        if not symbol:
            return []

        # Extract calls
        calls = self._extract_calls(symbol)
        return [name for name, _ in calls]

    def get_dependency_graph(self, symbols: List[Dict]) -> Dict[str, Dict]:
        """
        Build a complete dependency graph.

        Args:
            symbols: List of all symbols

        Returns:
            Dict mapping symbol names to their dependencies
        """
        self.symbol_map = {s['name']: s for s in symbols}

        graph = {}

        for symbol in symbols:
            calls = self._extract_calls(symbol)
            callees = [
                name for name, _ in calls
                if name in self.symbol_map and name != symbol['name']
            ]
            graph[symbol['name']] = {
                'calls': callees,
                'called_by': []
            }

        # Populate reverse dependencies (called_by)
        for caller_name, deps in graph.items():
            for callee_name in deps['calls']:
                if callee_name in graph:
                    graph[callee_name]['called_by'].append(caller_name)

        return graph
