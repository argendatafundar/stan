from ...common import get_flags
from .parse_imports import parse_imports

EXTERNAL_DEPENDENCY_TOKEN = '#@'

def get_github_dependencies_by_line(text: str):
    return get_flags(text, EXTERNAL_DEPENDENCY_TOKEN)

def get_github_dependencies(text: str, dependencies: None|set[str] = None):
    dependencies = dependencies or set()
    by_line = get_github_dependencies_by_line(text)
    lines = text.splitlines()

    for i, tokens in by_line.items():
        line = lines[i]
        imports = parse_imports(line)
        
        if len(imports) > 1:
            raise ValueError(f"Multiple imports in line {i} ({line}): {imports}")

        import_name = imports[0]

        dependencies.discard(import_name)

        for token in tokens:
            dependencies.add(f'{import_name}@{token}')
    return dependencies