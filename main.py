from argendata_stan.script.python import ScriptPython

script = """\
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

script = ScriptPython.from_source(filename='script.py', source=script, project_name='test-project')
print(script)
# filename='another_output_output.csv' datetime=datetime.datetime(2025, 12, 13, 20, 43, 27, 234557) environment=EnvironmentPython(dependencies=['pandas', 'argendata_datasets@git+https://github.com/joangq/argendatafundar-datasets.git'], checksum='7c62316862901e25795a679205d74a1f4abe24e9729e27b48d61b17880f1c049') produces=['R1C1(output.csv@sha1:943a702d06f34599aee1f8da8ef9f7296031d699)', 'R1C2(another_output_output.csv@sha1:180e041de4381fb718f03c440e697e0ca7fa8a0b)'] consumes=['R1C0@latest']