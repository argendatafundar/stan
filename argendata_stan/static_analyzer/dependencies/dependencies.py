import ast
import sys
import re
from typing import TypedDict
from ...common import ConfigFlags, AnalyzerFunc, get_flags
from .parse_imports import parse_imports
from .github import get_github_dependencies

IMPORT_TOKEN = "#'"
def get_dependencies_by_line(text: str):
    return get_flags(text, IMPORT_TOKEN)

analyze_dependencies: AnalyzerFunc[dict]
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

ENVIRONMENT_TOKEN = "#^"
def parse_environment(text: str):
    flags = get_flags(text, ENVIRONMENT_TOKEN)
    
    if len(flags) != 1:
        raise ValueError(f"Expected exactly one environment flag in {text}, got {len(flags)}")
    
    env = flags.get(0)
    
    if env is None:
        raise ValueError(f"Null environment flag in {text}")

    try:
        import pathlib
        env = pathlib.Path(env)
    except Exception as e:
        import traceback
        exception = traceback.format_exc()
        raise ValueError(f"{exception}\nEnvironment flag must be a valid path: {env!r}")

    return env

analyze_dependencies: AnalyzerFunc[dict]
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
    
    if config.parse_environment:
        result['environment'] = parse_environment(text)

    return result