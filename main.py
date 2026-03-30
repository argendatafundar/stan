from dataclasses import dataclass, field

from lamedh.workspace import UvWorkspace

@dataclass
class ExternalDependency:
    package: str
    url: str

    def __str__(self):
        return f'{self.package}@{self.url}'

    def as_source(self):
        return {self.package: str(self)}

@dataclass
class GithubDependency(ExternalDependency):
    package: str
    owner: str
    repo: None|str = None
    url: str = field(
        init=False,
        default_factory=lambda: 'git+https://github.com/{owner}/{repo}.git'
    )

    def __post_init__(self):
        self.repo = self.repo or self.package

        self.url = self.url.format(
            owner = self.owner,
            repo = self.repo
        )

known_sources = {
    ** ( GithubDependency(
            package='argendata_api', 
            owner='argendatafundar', 
            repo='internal-api').as_source()
            
       | GithubDependency('argendata_stan', 'joangq').as_source()
       | GithubDependency('argendata_datasets', 'joangq').as_source()
       )
}

from pathlib import Path
from lamedh import PythonScript, UvRunner

SAMPLE_SCRIPT = Path(__file__).parent / 'test' / 'files' / 'sample_script.py'

script = PythonScript.from_content(
    content = SAMPLE_SCRIPT.read_text(), 
    known_sources = known_sources
)

EXPORT_LINES = \
"""\

from argendata_datasets import Datasets
from pathlib import Path

DATASETS_METADATA_PATH = Path(__file__).parent / 'datasets_metadata.json'
DATASETS_METADATA_PATH.write_text(Datasets.model_dump_json(indent=2))
"""


modified_script = PythonScript.from_content(
    content = script.content + EXPORT_LINES,
    known_sources = known_sources
)

print(modified_script.dependencies)

import dotenv as dotenv_lib

workspace = UvWorkspace.from_tempdir(delete=False)
tempdir = workspace.__tempdir__
workspace.__tempdir__ = None

dotenv = dotenv_lib.dotenv_values(Path(__file__).parent/'test'/'files'/'sample.env')
runner = UvRunner(dotenv=dotenv, verbose=True)

result = modified_script.run(space=workspace,runner=runner)

import json
datasets_metadata = json.loads(workspace['datasets_metadata.json'].read_text(encoding='utf8'))
print(datasets_metadata)

registry = datasets_metadata['registry']
exports = datasets_metadata['exports']

if not len(registry.keys()) == len(exports):
    print('Registry length mismatch')
    tempdir.cleanup()
    exit(1)

for k,v in registry.items():
    filename = v['filename']
    expected_path = (Path(tempdir.name)/filename)
    if not expected_path.exists():
        print(f'File {expected_path} not found')
    else:
        print(f'File {filename} found')

tempdir.cleanup()