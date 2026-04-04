from argendata_datasets import Dataset #' +argendata_api, +python-dotenv
from pathlib import Path

output = Path('output/test.txt')
output.parent.mkdir(parents=True, exist_ok=True)

Dataset.ABC.register(filepath=str(output), version='1.0.0')

Dataset.ABC.save(
    output.write_text('Hello, World!')
)