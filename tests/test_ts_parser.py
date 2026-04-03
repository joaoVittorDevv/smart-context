"""
Phase 2: Comparative tests — TreeSitterParser vs SimpleCodeParser.

Runs both parsers on the project's own source files and compares output.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.indexer.simple_parser import SimpleCodeParser
from src.indexer.ts_parser import TreeSitterParser


def compare_parsers(file_path: str):
    """Compare output of both parsers on a single file."""
    regex_parser = SimpleCodeParser('python')
    ts_parser = TreeSitterParser('python')

    regex_symbols = regex_parser.parse_file(file_path)
    ts_symbols = ts_parser.parse_file(file_path)

    regex_names = {s['name'] for s in regex_symbols}
    ts_names = {s['name'] for s in ts_symbols}

    only_regex = regex_names - ts_names
    only_ts = ts_names - regex_names
    common = regex_names & ts_names

    return {
        'file': os.path.basename(file_path),
        'regex_count': len(regex_symbols),
        'ts_count': len(ts_symbols),
        'common': len(common),
        'only_regex': only_regex,
        'only_ts': only_ts,
        'ts_symbols': ts_symbols,
    }


def test_synthetic_cases():
    """Test synthetic code snippets."""
    ts = TreeSitterParser('python')

    cases = [
        # 1. Simple class
        (b"class Foo:\n    pass\n", ['Foo'], ['class']),
        # 2. Class with inheritance
        (b"class Bar(Base):\n    pass\n", ['Bar'], ['class']),
        # 3. Class with decorator
        (b"@dataclass\nclass Cfg:\n    x: int = 1\n", ['Cfg'], ['class']),
        # 4. Top-level function
        (b"def hello():\n    return 1\n", ['hello'], ['function']),
        # 5. Async function
        (b"async def fetch():\n    await x()\n", ['fetch'], ['function']),
        # 6. Method inside class
        (b"class A:\n    def do(self):\n        pass\n", ['A', 'do'], ['class', 'method']),
        # 7. Static method
        (b"class B:\n    @staticmethod\n    def run():\n        pass\n", ['B', 'run'], ['class', 'method']),
        # 8. Multiple classes and functions
        (
            b"class X:\n    pass\n\nclass Y:\n    pass\n\ndef z():\n    pass\n",
            ['X', 'Y', 'z'],
            ['class', 'class', 'function'],
        ),
        # 9. Empty file
        (b"", [], []),
        # 10. Only imports
        (b"import os\nfrom pathlib import Path\n", [], []),
    ]

    print("=" * 60)
    print("SYNTHETIC TESTS")
    print("=" * 60)

    passed = 0
    failed = 0

    for i, (code, expected_names, expected_types) in enumerate(cases, 1):
        symbols = ts.parse_code(code, f'case_{i}.py')
        actual_names = [s['name'] for s in symbols]
        actual_types = [s['type'] for s in symbols]

        names_ok = actual_names == expected_names
        types_ok = actual_types == expected_types

        status = "✅" if (names_ok and types_ok) else "❌"
        if names_ok and types_ok:
            passed += 1
        else:
            failed += 1

        print(f"  {status} Case {i}: names={actual_names} types={actual_types}")
        if not names_ok:
            print(f"     Expected names: {expected_names}")
        if not types_ok:
            print(f"     Expected types: {expected_types}")

    print(f"\nSynthetic: {passed}/{passed + failed} passed\n")
    return failed == 0


def test_real_files():
    """Test on real project files."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    # Go up one level since tests/ is inside the project root
    project_root = os.path.dirname(project_root)
    src_dir = os.path.join(project_root, 'src')

    py_files = []
    for root, dirs, files in os.walk(src_dir):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if f.endswith('.py'):
                full = os.path.join(root, f)
                # Skip empty files
                if os.path.getsize(full) > 10:
                    py_files.append(full)

    # Also test main.py
    main_py = os.path.join(project_root, 'main.py')
    if os.path.exists(main_py):
        py_files.append(main_py)

    print("=" * 60)
    print("REAL FILE COMPARISON (Regex vs Tree-sitter)")
    print("=" * 60)

    total_regex = 0
    total_ts = 0
    all_ok = True

    for fpath in sorted(py_files):
        result = compare_parsers(fpath)
        total_regex += result['regex_count']
        total_ts += result['ts_count']

        status = "✅" if not result['only_regex'] else "⚠️"
        print(f"  {status} {result['file']}: regex={result['regex_count']} ts={result['ts_count']} common={result['common']}")

        if result['only_regex']:
            print(f"     Only in regex: {result['only_regex']}")
            all_ok = False
        if result['only_ts']:
            print(f"     Only in tree-sitter: {result['only_ts']}")

    print(f"\nTotal: regex={total_regex} | tree-sitter={total_ts}")
    print(f"Tree-sitter found {'MORE' if total_ts > total_regex else 'LESS' if total_ts < total_regex else 'SAME'} symbols")

    # Show detail of tree-sitter symbols for verification
    print("\n" + "=" * 60)
    print("TREE-SITTER SYMBOL DETAILS")
    print("=" * 60)
    for fpath in sorted(py_files):
        ts = TreeSitterParser('python')
        symbols = ts.parse_file(fpath)
        if symbols:
            fname = os.path.basename(fpath)
            print(f"\n  📄 {fname}:")
            for s in symbols:
                print(f"    {s['type']:10s} {s['name']:30s} L{s['start_line']}-{s['end_line']}")

    return all_ok


if __name__ == '__main__':
    print("🧪 Tree-sitter Parser Comparative Tests\n")

    synth_ok = test_synthetic_cases()
    real_ok = test_real_files()

    print("\n" + "=" * 60)
    if synth_ok and real_ok:
        print("✅ ALL TESTS PASSED!")
    elif synth_ok:
        print("⚠️  Synthetic passed, some differences in real files (review above)")
    else:
        print("❌ FAILURES DETECTED")
    print("=" * 60)
