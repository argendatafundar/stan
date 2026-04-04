import json
from utils import script_from_content_test, script_run_test, scripts
from argendata_stan import Workspace
from argendata_datasets import Datasets

import pytest
import shutil
from pathlib import Path

# on startup
@pytest.fixture(scope='session', autouse=True)
def setup():
    for x in Path(__file__).parent.parent.glob('**/tmp*'):
        if x.is_dir():
            print(f'Removing {x}')
            shutil.rmtree(x)
    yield

def test_hello_world():
    script = script_from_content_test(scripts.path.hello_world.read_text())

    script_run_test(script, verbose=False)

def test_no_dep():
    script = script_from_content_test(scripts.path.no_dep.read_text())

    script_run_test(script, verbose=False)

def test_dotenv():
    script = script_from_content_test(scripts.path.dotenv.read_text())
    
    space = Workspace.from_tempdir(cleanup=False, delete=False)
    space['.env'].write_text("SOME_KEY=SOME_VALUE")
    result = script_run_test(script, space=space, verbose=False)
    datasets_metadata = (
        Datasets._Representation.model_validate_json(
            space['datasets_metadata.json'].read_text()
        )
    )

    assert set(datasets_metadata.registry.keys()) == set(datasets_metadata.exports)
    assert 'DOTENV' in datasets_metadata.registry.keys()

    filepath = datasets_metadata.registry['DOTENV']['filepath']
    assert filepath == 'dotenv_data'
    
    data = json.loads(space[filepath].read_text())
    assert data['SOME_KEY'] == 'SOME_VALUE'

def test_expected():
    script = script_from_content_test(scripts.path.expected.read_text())
    space = Workspace.from_tempdir(cleanup=False, delete=False)

    script_run_test(script, space=space, verbose=False)