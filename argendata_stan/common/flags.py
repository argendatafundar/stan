from typing import Callable, Any
import re

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