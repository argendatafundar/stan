import lamda.python
from lamda.python import GithubDependency
from packaging.requirements import Requirement

EXPORT_LINES = \
"""\
from argendata_datasets import Datasets
from pathlib import Path

DATASETS_METADATA_PATH = Path(__file__).parent / 'datasets_metadata.json'
DATASETS_METADATA_PATH.write_text(Datasets.model_dump_json(indent=2))
"""

class Script(lamda.python.Script):
    known_sources = {
        **  ( GithubDependency('argendata-stan', 'argendatafundar', 'stan').as_source()
            | GithubDependency('argendata-datasets', 'argendatafundar', 'datasets').as_source()
            | GithubDependency('argendata-internal-client', 'argendatafundar', 'internal-client').as_source()
            | GithubDependency('argendata-utils', 'argendatafundar', 'utils').as_source()
            ),
        
        # Retrocompatibility alias
        'argendata_api': 'argendata-internal-client@git+https://github.com/argendatafundar/internal-client'
    }

    def __post_init__(self):
        result = super().__post_init__()
        self.content += EXPORT_LINES
        self.dependencies = type(self).get_dependencies(self.content)
        return result
    

    def __post_init__(self):
        result = super().__post_init__()
        self.content += EXPORT_LINES
        self.dependencies = type(self).get_dependencies(self.content)
        return result
    
    @staticmethod
    def get_dependencies(content: str, **kwargs: object):
        known_sources = Script.known_sources.copy()
        external_sources = kwargs.get('known_sources') or {}
        known_sources.update(external_sources)
        analyzed_deps =  lamda.python.Script.get_dependencies(content, known_sources=known_sources)
        
        return analyzed_deps
