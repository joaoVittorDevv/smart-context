"""
Test System Languages Extraction (Go and Rust) directly against TreeSitterParser.
Ensures we have systems symbols accurately tracked (structs, traits, methods).
"""

from src.indexer.ts_parser import TreeSitterParser

def run_tests():
    parser = TreeSitterParser() # Dynamic parser
    
    cases = [
        # GO: struct and interface
        (
            b"package main\ntype User struct{}\ntype Auth interface{}\n",
            'test.go',
            ['User', 'Auth'],
            ['class', 'class']
        ),
        # GO: functions and methods
        (
            b"package main\nfunc Do() {}\nfunc (u *User) Get() {}\n",
            'test.go',
            ['Do', 'Get'],
            ['function', 'method']
        ),
        # RUST: struct and trait
        (
            b"struct User { id: i32 }\ntrait Auth { fn login(&self); }\n",
            'test.rs',
            ['User', 'Auth'],
            ['class', 'class']
        ),
        # RUST: function and impl methods
        (
            b"fn do_it() {}\nimpl User { fn get(&self) {} }\n",
            'test.rs',
            ['do_it', 'get'],
            ['function', 'method']
        ),
    ]

    print("=" * 60)
    print("SYS (Go/Rust) TESTS")
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

    print(f"\nSys Tests: {passed}/{passed + failed} passed\n")
    return failed == 0

if __name__ == '__main__':
    run_tests()
