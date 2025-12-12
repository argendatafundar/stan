from typing import override
from pydantic import BaseModel, Field
from .common import Environment, Script, ExecutionResult
import hashlib, json
from datetime import datetime as dt
import shutil
import pathlib
from ev import Ev
import tomllib, tomli_w

def pyproject_base(
    name: str,
    dependencies: list[str],
    version: str = '0.1.0',
    description: str = 'Add your description here',
    readme: str = 'README.md',
    requires_python: None|str = None,
): 
    if not requires_python:
        import sys
        requires_python = f">={sys.version_info.major}.{sys.version_info.minor}"
    
    return {
        'project': {
            'name': name, 
            'version': version, 
            'description': description, 
            'readme': readme, 
            'requires-python': requires_python, 
            'dependencies': dependencies
            }
    }

def python_environment_checksum(data: dict) -> str:
    return hashlib.sha256(json.dumps(data).encode()).hexdigest()

class EnvironmentPython(Environment):
    pyproject: dict = Field(..., repr=False)
    checksum: str = Field(default_factory=python_environment_checksum)
    dependencies: list[str] = Field(..., repr=True)

    @classmethod
    def load(cls, path: str) -> 'EnvironmentPython':
        import tomllib, pathlib
        pyproject = tomllib.loads(pathlib.Path(path).read_text())
        return cls(pyproject=pyproject, dependencies=pyproject['project']['dependencies'])
    
    @classmethod
    def from_dependencies(
        cls, 
        dependencies: list[str], *, 
        name: str, 
        version: str = '0.1.0', 
        description: str = 'Add your description here', 
        readme: str = 'README.md', 
        requires_python: None|str = None) -> 'EnvironmentPython':
        kwargs = locals()
        kwargs.pop('cls')
        pyproject = pyproject_base(**kwargs)
        
        return cls(pyproject=pyproject, dependencies=dependencies)

class ScriptPython(Script):
    environment: EnvironmentPython = Field(default_factory=EnvironmentPython)
    consumes: list[str] = Field(..., description='A list of datasets with version hashes that the script consumes.')

    @classmethod
    def load(cls, script_path: str, environment_path: str, produces: list[str], consumes: list[str]) -> 'ScriptPython':
        environment = EnvironmentPython.load(environment_path)
        return super().load(script_path, environment, produces, consumes)

    @classmethod
    def from_dependencies(
        cls,
        script_filename: str,
        script_content: str,
        dependencies: list[str],
        produces: list[str],
        consumes: list[str],
        project_name: str,
        *,
        project_version: str = '0.1.0',
        project_description: str = 'Add your description here',
        project_readme: str = 'README.md',
        project_requires_python: None|str = None,
    ):
        environment = EnvironmentPython.from_dependencies(
            dependencies=dependencies,
            name=project_name,
            version=project_version,
            description=project_description,
            readme=project_readme,
            requires_python=project_requires_python,
        )
        
        return cls(
            filename=script_filename,
            contents=script_content,
            datetime=dt.now(),
            environment=environment,
            produces=produces,
            consumes=consumes,
        )

    def _run(self, cwd: str):
        cwd = pathlib.Path(cwd)
        pyproject_path = cwd / "pyproject.toml"

        ev = Ev(
            cwd=cwd,
            debug=True,
        )

        assert not pyproject_path.exists(), f"pyproject.toml already exsits: {pyproject_path.resolve()}"

        ev.init('python', makedirs=False)

        if not (pathlib.Path(cwd) / 'pyproject.toml').exists():
            raise FileNotFoundError("'pyproject.toml' not found")
        
        # dump the pyproject.toml to the current directory
        (pathlib.Path(cwd) / 'pyproject.toml').write_text(
            tomli_w.dumps(self.environment.pyproject)
        )

        # check round-trip consistency
        is_same = (lambda:
            tomllib.loads(tomli_w.dumps(self.environment.pyproject)) \
                == self.environment.pyproject
        )

        assert is_same(), "Round-trip consistency check failed"

        # sync the environment
        ev.sync()

        # dump the script to the current directory
        (pathlib.Path(cwd) / self.filename).write_text(self.contents)

        # run the script
        result = ev.run(
            target=self.filename,
            language='python',
        )

        products = [
            pathlib.Path(cwd) / product
            for product in self.produces
        ]

        return ExecutionResult(
            process=result, 
            product=products
        )

    @override
    def run(self, cwd: None|str = None):
        """
        Ejecuta el script en una carpeta y devuelve el resultado del proceso
        junto con el producto del script.

        Si cwd es None, se crea una carpeta temporal y se ejecuta el script en ella.
        El output queda en la carpeta temporal y se devuelve el path del output.
        """
        is_temp = cwd is None

        if is_temp:
            import tempfile
            cwd = tempfile.mkdtemp()
        
        try:
            result = self._run(cwd)
            cwd = pathlib.Path(cwd)

            products = result.product

            if is_temp:
                newtmp = tempfile.mkdtemp(prefix=f'{self.filename.replace('.', '-')}_')
                products = [
                    pathlib.Path(shutil.move(
                        product, 
                        cwd.parent / newtmp / product.name
                    ))

                    for product in products
                ]

            products_dict = dict[str, pathlib.Path]()

            for p in self.produces:
                candidates = filter(
                    lambda file: file.name == p,
                    (file for file in products if file.exists() and file.is_file())
                )

                candidates = list(candidates)

                if len(candidates) == 0:
                    raise FileNotFoundError(f"Product {p} not found")

                assert len(candidates) == 1, f"Multiple products found for {p}"
                products_dict[p] = candidates[0]

            return ExecutionResult(
                process=result.process, 
                product=products_dict
            )
        
        finally:
            if is_temp:
                shutil.rmtree(cwd)

        
        
