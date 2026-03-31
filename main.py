from argendata_datasets import Datasets
from argendata_stan import Script, Workspace, Runner
from dotenv import dotenv_values
from pathlib import Path

SAMPLE_SCRIPT = Path(__file__).parent / 'test' / 'files' / 'sample_script.py'

script = Script.from_content(content = SAMPLE_SCRIPT.read_text())

workspace = Workspace.from_tempdir(cleanup=False, delete=False)
assert workspace.tempdir is not None

dotenv = dotenv_values(Path(__file__).parent/'test'/'files'/'sample.env')
runner = Runner(dotenv=dotenv, verbose=True)

result = runner.run(script, space=workspace)

metadata = result.datasets_metadata

print(metadata)

if not len(metadata.registry.keys()) == len(metadata.exports):
    print('Registry length mismatch')
    workspace.tempdir.cleanup()
    exit(1)

for k,v in metadata.registry.items():
    filename: str = v.filename
    expected_path = Path(workspace.tempdir.name) / filename

    if not expected_path.exists():
        print(f'File {expected_path} not found')
    else:
        print(f'File {filename} found')

workspace.tempdir.cleanup()