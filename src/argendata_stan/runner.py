from typing import cast, override
from lamedh.python import Script as PythonScript, UvRunner, UvWorkspace
from lamedh.common.files import Dotenv
from dataclasses import dataclass
from subprocess import CompletedProcess
from argendata_datasets import Datasets

@dataclass
class Result:
    completed_process: CompletedProcess
    datasets_metadata: Datasets._Representation

class Runner(UvRunner):
    @override
    def space_run(space: UvWorkspace, verbose: bool = False, **kwargs: object):
        result = UvRunner.space_run(space, verbose, **kwargs)
        datasets_metadata_json = space['datasets_metadata.json'].read_text(encoding='utf8')
        datasets_metadata = Datasets._Representation.model_validate_json(datasets_metadata_json)
        return Result(
            completed_process=result, 
            datasets_metadata=datasets_metadata
        )
    
    @override
    def run(self, script: PythonScript, space: None | UvWorkspace = None, dotenv: None | Dotenv | dict = None, verbose: None | bool = None):
        return cast(Result, super().run(script, space, dotenv, verbose))