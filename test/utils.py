from pathlib import Path
from typing import Iterable
from argendata_stan import Script
from packaging.requirements import Requirement
import subprocess

FILES_DIR = Path(__file__).parent / 'files'

class scripts:
    class path:
        expected    = FILES_DIR / 'expected_script.py'
        no_dep      = FILES_DIR / 'no_dep_script.py'
        hello_world = FILES_DIR / 'hello_world_script.py'
        dotenv      = FILES_DIR / 'dotenv_script.py'

def ran_successfully(result: object):
    if not isinstance(result, subprocess.CompletedProcess):
        return False
    
    if result.returncode != 0:
        raise AssertionError(result.stderr.decode('utf8'))
    
    return True

def all_isinstance(typ: type, iterable: Iterable):
    for x in iterable:
        if not isinstance(x, typ):
            return False
    
    return True

def script_from_content_test(content: str):
    script = Script.from_content(content)
    assert all_isinstance(Requirement, script.dependencies)
    return script

def script_run_test(script: Script, **run_kwargs):
    result = script.run(**run_kwargs)
    assert ran_successfully(result)
    return result