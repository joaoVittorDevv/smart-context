"""
Test Enterprise Languages Extraction (Java and C++) directly against TreeSitterParser.
Ensures we have systems symbols accurately tracked (classes, interfaces, methods).
"""

from src.indexer.ts_parser import TreeSitterParser

def run_tests():
    parser = TreeSitterParser() # Dynamic parser
    
    cases = [
        # JAVA: class and interface
        (
            b"package com.example;\npublic class User {}\ninterface Base {}\n",
            'test.java',
            ['User', 'Base'],
            ['class', 'class']
        ),
        # JAVA: methods
        (
            b"class Auth { public void login() {} }\n",
            'test.java',
            ['Auth', 'login'],
            ['class', 'method']
        ),
        # C++: class and struct
        (
            b"namespace core { class User {}; struct Data {}; }\n",
            'test.cpp',
            ['User', 'Data'],
            ['class', 'class']
        ),
        # C++: functions and methods
        (
            b"void start() {}\nclass App { void run(); void stop() {} };\n",
            'test.cpp',
            ['start', 'App', 'run', 'stop'],
            ['function', 'class', 'method', 'method']
        ),
    ]

    print("=" * 60)
    print("ENTERPRISE (Java/C++) TESTS")
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

    print(f"\nEnterprise Tests: {passed}/{passed + failed} passed\n")
    return failed == 0

if __name__ == '__main__':
    run_tests()
