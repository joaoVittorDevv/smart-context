import tree_sitter_typescript
from tree_sitter import Language, Parser

lang = Language(tree_sitter_typescript.language_typescript())
parser = Parser(lang)

src = b"""
interface User { name: string; }
type UserID = string;
export class Admin implements User {
  name: string = 'root';
  async ping(): Promise<boolean> { return true; }
}
"""
tree = parser.parse(src)

def print_tree(node, depth=0):
    indent = "  " * depth
    if node.is_named:
        name_node = node.child_by_field_name('name')
        name = name_node.text.decode('utf-8') if name_node else ''
        print(f"{indent}{node.type} | name: {name}")
    for child in node.children:
        print_tree(child, depth + 1)

print_tree(tree.root_node)
