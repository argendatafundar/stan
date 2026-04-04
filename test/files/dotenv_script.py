from argendata_datasets import Dataset
import dotenv #' python-dotenv
from pathlib import Path
import json

Dataset.DOTENV.register(filepath='dotenv_data')
Dataset.DOTENV.save(Path('dotenv_data').write_text(json.dumps(dotenv.dotenv_values())))