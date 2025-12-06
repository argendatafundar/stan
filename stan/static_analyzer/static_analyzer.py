from dataclasses import dataclass, asdict
from functools import reduce
from operator import or_ as union
import re
import sys


DATACLASS_CONFIG = dict(
    init         = True,
    repr         = True, 
    eq           = True, 
    order        = False,
    unsafe_hash  = False, 
    frozen       = True, 
    match_args   = True,
    kw_only      = True, 
    slots        = True, 
    weakref_slot = False,
)

@dataclass(**DATACLASS_CONFIG)
class ConfigFlags:
    parse_imports: bool = False
    parse_datasets: bool = False

    def __post_init__(self):
        if self.parse_datasets:
            import argendata_datasets

def get_flags(text: str, token: str):
    lines = text.splitlines()
    flags = dict[int, set[str]]()
    """
    Dictionary that holds flags as keys and line indices as values.
    """

    for i, line in enumerate(lines):
        if token in line:
            clean = line.split(token)[1].strip()
            # replace multiple spaces with a single space
            clean = re.sub(r'\s+', '', clean)
            clean = clean.split(',')
            for x in clean:
                flags.setdefault(i, set()).add(x)
    
    return flags

CONFIG_TOKEN = "#%"
def get_config(text: str):
    return get_flags(text, CONFIG_TOKEN)

def detect_config(text: str):
    flags = get_config(text)
    flags: set[str] = reduce(union, flags.values(), set())
    config: dict[str, bool] = {
        flag: (flag in flags)
        for flag in ConfigFlags.__annotations__
    }
    return ConfigFlags(**config)

def parse_imports(text: str):
    import ast
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

IMPORT_TOKEN = "#'"
def get_dependencies_by_line(text: str):
    return get_flags(text, IMPORT_TOKEN)

# TODO
def get_dependencies(text: str, magic_flags: "None|MagicFlags" = None):
    dependencies = set()
    magic_flags = magic_flags or MagicFlags()

    if magic_flags.parse_imports:
        imported = parse_imports(text)
        dependencies.update(imported)
    
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

class StaticAnalyzer:
    config: ConfigFlags

    def __init__(self, config: None|ConfigFlags=None):
        self.config = config or ConfigFlags()
    
    def run(self, code: str, detect_config: bool = True):
        if detect_config:
            self.config = detect_config(code)
        
        if self.config.parse_imports:
            ...
        
        datasets = []
        if self.config.parse_datasets:
            from argendata_datasets.dsl.analyzer import get_datasets
            datasets = get_datasets(code)
            datasets = list(datasets)

        
        return {
            "datasets": datasets,
        }
    
