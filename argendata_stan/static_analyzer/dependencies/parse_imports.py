import ast

def parse_imports(text: str):
    tree = ast.parse(text)
    modules = []
    seen = set()

    for node in ast.walk(tree):
        # `import foo`, `import foo.bar as baz`
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if not name or name.startswith('.'):
                    continue  # skip weird/relative-like
                base = name.split('.', 1)[0]
                if base not in seen:
                    seen.add(base)
                    modules.append(base)

        # `from foo import bar`, `from foo.bar import baz`
        elif isinstance(node, ast.ImportFrom):
            # skip relative imports: from .foo import bar, from .. import x, etc.
            if node.level and node.level > 0:
                continue
            if not node.module:
                continue
            base = node.module.split('.', 1)[0]
            if base not in seen:
                seen.add(base)
                modules.append(base)

    return modules