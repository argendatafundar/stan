import ast
import sys
import re
from typing import TypedDict
from ..common import ConfigFlags, Analyzer, get_flags
from .parse_imports import parse_imports
from .github import get_github_dependencies

IMPORT_TOKEN = "#'"
def get_dependencies_by_line(text: str):
    return get_flags(text, IMPORT_TOKEN)

def get_dependencies(text: str, dependencies: None|set[str] = None):
    dependencies = dependencies or set()

    by_line = get_dependencies_by_line(text)
    lines = text.splitlines()

    for i, tokens in by_line.items():
        line = lines[i]
        line = re.sub(r'\s+', ' ', line)
        for token in tokens:
            force = token.startswith('+')
            clean_token = token.replace('+', '')
            seen = [
                x for x in dependencies 
                if x in line.split(' ')
            ]

            if len(seen) > 1:
                raise ValueError(f"Collision for '{clean_token}' in line {i} ({line}): {seen}")
            
            seen = seen[0] if seen else None

            if not seen:
                dependencies.add(clean_token)
            elif force:
                dependencies.add(clean_token)
            else:
                dependencies.remove(seen)
                dependencies.add(clean_token)

    return dependencies - set(sys.stdlib_module_names)


analyze_dependencies: Analyzer[dict]
def analyze_dependencies(text: str, config: ConfigFlags, result: dict):
    if not config.detect_dependencies:
        return result

    dependencies = set()

    if config.parse_imports:
        dependencies.update(parse_imports(text))

    dependencies = get_dependencies(text, dependencies)

    if config.parse_github_dependencies:
        dependencies.update(get_github_dependencies(text, dependencies))

    result["dependencies"] = dependencies

    return result