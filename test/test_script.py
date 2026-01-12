import rootdir
import pytest

from argendata_stan.script.common import Environment, Script
from argendata_stan.script.python import EnvironmentPython, ScriptPython
from argendata_stan.script.r import EnvironmentR, ScriptR
from datetime import datetime
import rich, pathlib, shutil
from ev import Ev

def test_abstract_field():
    with pytest.raises(TypeError):
        Script[Environment](
            filename='a', 
            contents='b', 
            datetime=datetime.now()
        )

def test_python_environment_load():
    pyproject = rootdir.ROOT_DIR
    environment = EnvironmentPython.load(pyproject)
    rich.print(environment)
    
def test_python_script_load():
    pyproject = rootdir.ROOT_DIR
    script_path = __file__
    script = ScriptPython.load(script_path, pyproject, produces=[], consumes=[])
    
    assert isinstance(script.environment, EnvironmentPython)

@pytest.mark.skip(reason="R scripts are not supported yet")
def test_r_script_load():
    cwd = pathlib.Path(rootdir.ROOT_DIR).parent / 'test'
    test_folder = cwd / 'r_test'
    ev = Ev(cwd)
    ev.init(language='r', target=test_folder, makedirs=True)
    ev.add('ggplot2', 'r', target=test_folder)

    script_path = test_folder / 'script.R'
    script_path.write_text('print("Hello, World!")')
    script = ScriptR.load(script_path, test_folder, produces=[], consumes=[])

    ev.run(script_path, language='r', cwd=test_folder)

    assert isinstance(script.environment, EnvironmentR)

    # Teardown
    ev.purge(language='r', force=True, target=test_folder)
    shutil.rmtree(test_folder)

def test_python_script_from_dependencies():
    script_filename = 'script.py'
    script_content = 'print("Hello, World!")'
    dependencies = ['numpy', 'pandas']

    
    script = ScriptPython.from_dependencies(
        script_filename=script_filename,
        script_content=script_content,
        dependencies=dependencies,
        project_name='test-python-script',
        produces=[],
        consumes=[],
    )

    rich.print(script)

    assert isinstance(script.environment, EnvironmentPython)

#run this specific test with `pytest -k test_python_script_run`
def test_python_script_run():
    script_content =\
"""
import urllib3
import polars as pl
import io
import sys

CSV_URL = "https://datahub.io/core/population/r/population.csv"

def download_csv(url: str) -> bytes:
    http = urllib3.PoolManager()
    resp = http.request("GET", url)
    if resp.status != 200:
        raise RuntimeError(f"Failed to download CSV: status {resp.status}")
    return resp.data

def main():
    try:
        data = download_csv(CSV_URL)
    except Exception as e:
        print("Error downloading CSV:", e, file=sys.stderr)
        sys.exit(1)

    df = pl.read_csv(
        io.BytesIO(data),
        schema_overrides={"Value": pl.Float64}
    )

    df2 = (
        df.filter(pl.col("Year") >= 2000)
          .rename({
             "Country Name": "country",
             "Country Code": "country_code",
             "Year": "year",
             "Value": "population"
          })
          .sort(["country", "year"])
    )

    df2.write_csv("output.csv")
    print("Written output.csv")

if __name__ == "__main__":
    main()
"""
    script_filename = 'script.py'
    dependencies = [
        'urllib3', 
        'polars',
        'rich', # TODO: Esta libreria deberia instalarse con polars. (?)
    ]

    script = ScriptPython.from_dependencies(
        script_filename=script_filename,
        script_content=script_content,
        dependencies=dependencies,
        project_name='test-python-script',
        produces=['output.csv'], # TODO: test nested folders
        consumes=[],
    )

    result = script.run()

    # rich.print(result)

    if result.process.is_failed():
        error = result.process.error
        traceback = error.traceback.decode("utf-8")
        rich.print(f'[red]{traceback}[/red]')
        raise Exception(traceback)

    output = result.product['output.csv']
    print(output)
    
    import csv

    with open(output, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        assert len(rows) > 0

@pytest.mark.skip(reason="Multiple outputs are not supported yet")
def test_script_from_source_with_datasets():
    script_source = """\
from argendata_datasets import Datasets #@ git+https://github.com/joangq/argendatafundar-datasets.git
import pandas as pd
import pathlib

x = Datasets.R1C0.get(version='latest')

FILENAME = 'output.csv'
dataset = Datasets.R1C1.register(
    filename=FILENAME,
    foo='a',
    bar=1,
)

dataset.save(pathlib.Path(FILENAME).write_text('Hello, world!'))

ANOTHER_FILENAME = f'another_output_{FILENAME}'
another_dataset = Datasets.R1C2.register(
    filename=ANOTHER_FILENAME,
    foo='b',
    bar=2,
)

another_dataset.save(pathlib.Path(ANOTHER_FILENAME).write_text('Hello, world!!'))
"""

    script = ScriptPython.from_source(
        filename='script.py',
        source=script_source,
        project_name='test-project'
    )

    assert script.filename == 'script.py'
    assert script.contents == script_source
    assert isinstance(script.environment.dependencies, list)
    assert 'pandas' in script.environment.dependencies
    assert 'argendata_datasets@git+https://github.com/joangq/argendatafundar-datasets.git' in script.environment.dependencies

    assert len(script.produces) == 2
    assert any('R1C1(output.csv@sha1:' in p for p in script.produces)
    assert any('R1C2(another_output_output.csv@sha1:' in p for p in script.produces)

    assert len(script.consumes) == 1
    assert script.consumes[0] == 'R1C0@latest'

