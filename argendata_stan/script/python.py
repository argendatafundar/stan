from typing import override, cast, Callable
from pydantic import BaseModel, Field
from .common import Environment, Script, ExecutionResult, Metadata
import hashlib, json
from datetime import datetime as dt
import shutil
import pathlib
from ev import Ev
import tomllib, tomli_w

from argendata_datasets.checksum import Hash, hash, digest

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

from ..dynamic_analyzer.datasets.datasets import ExportedDataset

class MetadataPython(Metadata):
    exported_datasets: list[ExportedDataset] = Field(default_factory=list)

def check_hash(hash, output_file):
    hash_method, hash_value = hash.split(':')
    #import hashlib
    hash: None|Callable[[bytes], str] = getattr(hashlib, hash_method, None)

    if hash is None:
        raise ValueError(f'Invalid hash method: {hash_method}')

    hash = cast(Callable[[bytes], str], hash)
    output_checksum = hash(output_file.read_bytes()).hexdigest()

    if output_checksum != hash_value:
        return False
    
    return True

class ScriptPython(Script):
    environment: EnvironmentPython = Field(default_factory=EnvironmentPython)
    metadata: MetadataPython = Field(default_factory=MetadataPython)

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
        script_metadata: None|MetadataPython = None,
    ):
        environment = EnvironmentPython.from_dependencies(
            dependencies=dependencies,
            name=project_name,
            version=project_version,
            description=project_description,
            readme=project_readme,
            requires_python=project_requires_python,
        )

        params = dict(
            filename=script_filename,
            contents=script_content,
            datetime=dt.now(),
            environment=environment,
            produces=produces,
            consumes=consumes,
        )

        if script_metadata is not None:
            params['metadata'] = script_metadata
        
        return cls(**params)

    @classmethod
    def _from_source(
        cls,
        partial,
        target,
        produced_datasets_filename,
        filename,
        source,
        project_name,
        dependencies,
        consumes,
    ):
        partial_result = partial.run(target_dir=target)

        if partial_result.process.is_failed():
            raise partial_result.process.error.exception
        
        product = partial_result.product[produced_datasets_filename]

        produced_datasets: list[dict] = json.loads(product.read_text())
        # [{'filename': ..., 'name': ..., **extra}]

        exported_datasets = []

        _produces = []
        for produced_dataset in produced_datasets:
            dataset_filename = produced_dataset.pop('filename')
            codigo = produced_dataset.pop('name')
            extra = produced_dataset

            file = pathlib.Path(target) / dataset_filename

            assert file.exists(), f"Produced dataset {dataset_filename} not found"

            #checksum = hashlib.sha1(file.read_bytes()).hexdigest()
            hashobj = digest.sha1(file)

            extra['checksum'] = hashobj.to_str(include_filename=False)
            extra['st_size'] = file.stat().st_size

            _produces.append(f'{codigo}({hashobj.to_str(include_filename=True)})')

            exported_datasets.append(ExportedDataset(
                filename=dataset_filename,
                codigo=codigo,
                metadata=extra,
            ))


        result = cls.from_dependencies(
            script_filename=filename,
            script_content=source,
            dependencies=list(dependencies),
            produces=_produces,
            consumes=[f'{x.name}@{x.version}' for x in consumes],
            project_name=project_name,
            script_metadata=MetadataPython(exported_datasets=exported_datasets),
        )

        if len(result.produces) == 0:
            raise ValueError('Script must produce at least one output')
        if len(result.produces) > 1:
            products_str = ', '.join(result.produces)
            raise ValueError(f'More than one output is not supported yet. Expected 1, Got {len(result.produces)}: {products_str}')
        
        produces = result.produces[0] # code(filename@hash)
        import re
        pattern = r'^([A-Za-z0-9]+)\(([^@()]+)@([^()]+)\)$'
        match = re.match(pattern, produces)
        if not match:
            raise ValueError(f'Invalid output format: {produces}')

        codigo, filename, hash = match.groups()
        output_file = pathlib.Path(target) / filename
        
        is_valid_hash = check_hash(hash, output_file)
        assert is_valid_hash

        return result

    @classmethod
    def from_source(
        cls,
        filename: str,
        source: str,
        project_name: str,
        config_flags: None|dict[str, bool] = None,
        target: None|str = None,
    ):
        from ..common import ConfigFlags
        from ..static_analyzer import StaticAnalyzer
        config_flags = config_flags or {
            'detect_dependencies': True,
            'parse_imports': True,
            'parse_github_dependencies': True,
            'detect_datasets': True,
            'detect_output_datasets': True,
        }

        config_flags = ConfigFlags(**config_flags)

        static_analyzer = StaticAnalyzer(config_flags)
        static_analysis = static_analyzer.run(source, detect_config=False)

        dependencies = static_analysis['dependencies']
        consumes = static_analysis['datasets']

        PRODUCED_DATASETS_FILENAME = 'produced_datasets.json'

        modified_source = source
        modified_source +=\
f"""\
from argendata_datasets.dsl.datasets import Client
import pathlib, json
pathlib.Path({PRODUCED_DATASETS_FILENAME!r}).write_text(json.dumps(Client().produced))
"""
        partial_result = cls.from_dependencies(
            script_filename=filename,
            script_content=modified_source,
            dependencies=list(dependencies),
            produces=[PRODUCED_DATASETS_FILENAME],
            consumes=[
                f'{x.name}@{x.version}'
                for x in consumes
            ],
            project_name=project_name,
        )

        from functools import partial as apply_args
        from typing import Callable, cast

        get_result = apply_args(
            cls._from_source,
            partial=partial_result,
            # target = _____
            produced_datasets_filename=PRODUCED_DATASETS_FILENAME,
            filename=filename,
            source=source,
            project_name=project_name,
            dependencies=dependencies,
            consumes=consumes,
        )

        if target is None:
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                return get_result(target=temp_dir)
        else:
            return get_result(target=target)
            

    def _run(self, target: str, verbose: bool = False):
        target = pathlib.Path(target)
        pyproject_path = target / "pyproject.toml"

        ev = Ev(
            cwd=target,
            debug=verbose,
        )

        assert not pyproject_path.exists(), f"pyproject.toml already exsits: {pyproject_path.resolve()}"

        ev.init('python', makedirs=False)

        if not (pathlib.Path(target) / 'pyproject.toml').exists():
            raise FileNotFoundError("'pyproject.toml' not found")
        
        # dump the pyproject.toml to the current directory
        (pathlib.Path(target) / 'pyproject.toml').write_text(
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
        (pathlib.Path(target) / self.filename).write_text(self.contents)

        # run the script
        result = ev.run(
            target=self.filename,
            language='python',
        )

        products = [
            pathlib.Path(target) / product
            for product in self.produces
        ]

        return ExecutionResult(
            process=result, 
            product=products
        )

    def _process_products(self, products: list[pathlib.Path]) -> dict[str, pathlib.Path]:
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

        return products_dict

    def _temp_run(self, verbose: bool = False):
        import tempfile
        target_dir = tempfile.mkdtemp(prefix=f'{self.filename.replace('.', '-')}_')
        result = self._run(target_dir, verbose)
        products = result.product
        return result, products

    @override
    def run(self, target_dir: None|str = None, verbose: bool = False):
        """
        Ejecuta el script en una carpeta y devuelve el resultado del proceso
        junto con el producto del script.

        Si target_dir es None, se crea una carpeta temporal y se ejecuta el script en ella.
        """
        if target_dir is None:
            result, products = self._temp_run(verbose)
        else:
            result = self._run(target_dir, verbose)
            products = result.product
        
        if result.process.is_failed():
            return ExecutionResult(
                process=result.process,
                product=None,
                error=result.process.error,
            )
        products_dict = self._process_products(products)

        return ExecutionResult(
            process=result.process, 
            product=products_dict
        )

        
        
