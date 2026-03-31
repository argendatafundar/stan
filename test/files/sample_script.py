from argendata_datasets import Dataset #' +argendata_api, +python-dotenv
from pathlib import Path

x = Dataset.R151C0.get()
print(x)
# Dataset.ABC.download(to='')

output = Path('output/test.txt')
output.parent.mkdir(parents=True, exist_ok=True)

Dataset.ABC.register(filename=str(output), version='1.0.0')

Dataset.ABC.save(
    output.write_text('Hello, World!')
)