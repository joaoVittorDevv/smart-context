"""
Phase 4: Omni-Repo Test.
Tests robust, simultaneous multi-language capabilities of the new indexer architecture without interference.
"""

from src.indexer.ts_parser import TreeSitterParser

def run_tests():
    parser = TreeSitterParser() # Polyglot parser
    
    files = [
        # Python
        (
            b"class PyServer:\n    def start(self):\n        pass\n\ndef py_init():\n    pass\n",
            "server.py",
            ['PyServer', 'start', 'py_init'],
            ['class', 'method', 'function']
        ),
        # JS/TS
        (
            b"export class JSServer {\n  start() {}\n}\nconst jsInit = () => {}\n",
            "server.ts",
            ['JSServer', 'start', 'jsInit'],
            ['class', 'method', 'function']
        ),
        # Go
        (
            b"package main\ntype GoServer struct {}\nfunc (s *GoServer) Start() {}\nfunc GoInit() {}\n",
            "server.go",
            ['GoServer', 'Start', 'GoInit'],
            ['class', 'method', 'function']
        ),
        # Rust
        (
            b"struct RsServer {}\nimpl RsServer {\n    fn start(&self) {}\n}\nfn rs_init() {}\n",
            "server.rs",
            ['RsServer', 'start', 'rs_init'],
            ['class', 'method', 'function']
        ),
        # Java
        (
            b"public class JavaServer {\n    public void start() {}\n    static void javaInit() {}\n}\n",
            "Server.java",
            ['JavaServer', 'start', 'javaInit'],
            ['class', 'method', 'method'] # Inside a Java class, everything is a method!
        ),
        # C++
        (
            b"class CppServer {\n  void start() {}\n};\nvoid cpp_init() {}\n",
            "server.cpp",
            ['CppServer', 'start', 'cpp_init'],
            ['class', 'method', 'function']
        ),
    ]

    print("=" * 60)
    print("OMNI-REPO (7 Languages) TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    total_symbols = 0

    for i, (code, file_path, expected_names, expected_types) in enumerate(files, 1):
        symbols = parser.parse_code(code, file_path)
        actual_names = [s['name'] for s in symbols]
        actual_types = [s['type'] for s in symbols]

        names_ok = actual_names == expected_names
        types_ok = actual_types == expected_types

        status = "✅" if (names_ok and types_ok) else "❌"
        if names_ok and types_ok:
            passed += 1
            total_symbols += len(symbols)
        else:
            failed += 1

        print(f"  {status} [{file_path}]: names={actual_names} types={actual_types}")
        if not names_ok:
            print(f"     Expected names: {expected_names}")
        if not types_ok:
            print(f"     Expected types: {expected_types}")

    print(f"\nOmni Tests: {passed}/{passed + failed} files parsed perfectly!")
    print(f"Total symbols extracted dynamically: {total_symbols}")
    return failed == 0

if __name__ == '__main__':
    run_tests()
