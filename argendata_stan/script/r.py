from typing import override
from pydantic import BaseModel, Field
from .common import Environment, Script
import json, hashlib, pathlib
from datetime import datetime as dt
from functools import reduce, partial
from operator import add

def r_environment_checksum(data: dict) -> str:
    renv_lock: str = data['renv_lock']
    r_profile: str = data['r_profile']
    renv_settings: str = data['renv_settings']
    activate: str = data['activate']

    renv_settings = json.dumps(json.loads(renv_settings))
    return hashlib.sha256(
        reduce(add, map(
            partial(str.encode, encoding='utf-8'), 
            (renv_lock, r_profile, renv_settings, activate))
        )
    ).hexdigest()


class EnvironmentR(Environment):
    """
    Source: https://rstudio.github.io/renv/articles/renv.html#collaboration
    """
    dependencies: list[str] = Field(..., repr=True)
    renv_lock: str = Field(
        ..., 
        title='renv.lock',
        description='The contents of the renv.lock file.',
        repr=False,
    )

    r_profile: str = Field(
        ..., 
        title='.Rprofile',
        description='The contents of the .Rprofile file.',
        repr=False,
    )

    renv_settings: str = Field(
        ..., 
        title='renv/settings.json',
        description='The contents of the renv/settings.json file.',
        repr=False,
    )

    activate: str = Field(
        ..., 
        title='renv/activate.R',
        description='The contents of the renv/activate.R file.',
        repr=False,
    )

    checksum: str = Field(default_factory=r_environment_checksum)

    @classmethod
    def load(cls, path: str) -> 'EnvironmentR':
        """
         Expected directory structure:

        - renv/
            - settings.json
            - activate.R
        - .Rprofile
        - renv.lock
        """
        r_profile_path = pathlib.Path(path) / '.Rprofile'
        renv_settings_path = pathlib.Path(path) / 'renv' / 'settings.json'
        renv_activate_path = pathlib.Path(path) / 'renv' / 'activate.R'
        renv_lock_path = pathlib.Path(path) / 'renv.lock'

        r_profile = r_profile_path.read_text(encoding='utf-8')
        renv_settings = renv_settings_path.read_text(encoding='utf-8')
        renv_activate = renv_activate_path.read_text(encoding='utf-8')
        renv_lock = renv_lock_path.read_text(encoding='utf-8')

        data = dict(
            renv_lock=renv_lock, 
            r_profile=r_profile, 
            renv_settings=renv_settings, 
            activate=renv_activate
        )

        checksum = r_environment_checksum(data)

        return cls(
            renv_lock=renv_lock, 
            r_profile=r_profile, 
            renv_settings=renv_settings, 
            activate=renv_activate,
            checksum=checksum,
            dependencies=[] # TODO: Implementar
        )

    @classmethod
    def from_dependencies(cls, dependencies: list[str]) -> 'EnvironmentR':
        import tempfile
        from ev import Ev
        import shutil

        tempdir = tempfile.mkdtemp()
        
        ev = Ev(tempdir)
        ev.init('r', target=tempdir)

        for dependency in dependencies:
            ev.add(dependency, 'r', target=tempdir)
        
        result = cls.load(tempdir)
        result.dependencies = dependencies
        ev.purge(language='r', force=True, target=tempdir)
        shutil.rmtree(tempdir)
        return result

    

class ScriptR(Script):
    environment: EnvironmentR = Field(default_factory=EnvironmentR)
    consumes: list[str] = Field(..., description='A list of datasets with version hashes that the script consumes.')

    @classmethod
    def load(cls, script_path: str, target_dir: str, produces: list[str], consumes: list[str]) -> 'ScriptR':
        """
        Expected directory structure:
        - renv/
            - settings.json
            - activate.R
        - .Rprofile
        - renv.lock

        Args:
            - script_path: the path to the script file
            - target_dir: the directory where either '.Rprofile', 'renv/' or 'renv.lock' files are located.
        """

        return super().load(
            script_path=script_path,
            environment=EnvironmentR.load(target_dir),
            produces=produces,
            consumes=consumes,
        )

    @classmethod
    def from_dependencies(
        cls,
        script_filename: str,
        script_content: str,
        dependencies: list[str],
        produces: list[str],
        project_name: None|str = None,
        consumes: list[str] = [],
    ):
        environment = EnvironmentR.from_dependencies(dependencies=dependencies)
        
        return cls(
            filename=script_filename,
            contents=script_content,
            datetime=dt.now(),
            environment=environment,
            produces=produces,
            consumes=consumes,
        )
    
    @override
    def run(self, cwd: None|str = None):
        # TODO: Implementar esta funcion.
        raise NotImplementedError("Running R scripts is not implemented yet")