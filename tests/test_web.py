"""
Test Web Extraction (JS and TS) directly against TreeSitterParser.
Ensures we have web symbols accurately tracked before committing the feature.
"""

import os
from src.indexer.ts_parser import TreeSitterParser

def run_tests():
    parser = TreeSitterParser() # Dynamic parser
    
    cases = [
        # JavaScript basic functions and arrow functions
        (
            b"function doApples() { return 1; }\nconst doBananas = () => { return 2; }\n",
            'test.js',
            ['doApples', 'doBananas'],
            ['function', 'function']
        ),
        # JS Class and method
        (
            b"class Auth {\n  login(user) { return true; }\n}\n",
            'test.js',
            ['Auth', 'login'],
            ['class', 'method']
        ),
        # TS Interface and type
        (
            b"interface User { name: string; }\ntype UserID = string;\n",
            'test.ts',
            ['User', 'UserID'],
            ['class', 'class']
        ),
        # TS Class implementing interface + method
        (
            b"export class Admin implements User {\n  name: string = 'root';\n  async ping(): Promise<boolean> { return true; }\n}\n",
            'test.ts',
            ['Admin', 'ping'],
            ['class', 'method']
        ),
    ]

    print("=" * 60)
    print("WEB (JS/TS) TESTS")
    print("=" * 60)

    passed = 0
    failed = 0

    for i, (code, file_path, expected_names, expected_types) in enumerate(cases, 1):
        symbols = parser.parse_code(code, file_path)
        actual_names = [s['name'] for s in symbols]
        actual_types = [s['type'] for s in symbols]

        names_ok = actual_names == expected_names
        types_ok = actual_types == expected_types

        status = "✅" if (names_ok and types_ok) else "❌"
        if names_ok and types_ok:
            passed += 1
        else:
            failed += 1

        print(f"  {status} Case {i} ({file_path}): names={actual_names} types={actual_types}")
        if not names_ok:
            print(f"     Expected names: {expected_names}")
        if not types_ok:
            print(f"     Expected types: {expected_types}")

    print(f"\nWeb Tests: {passed}/{passed + failed} passed\n")
    return failed == 0

if __name__ == '__main__':
    run_tests()
