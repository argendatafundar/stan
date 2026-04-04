import lamda.python
from lamda.python import GithubDependency

EXPORT_LINES = \
"""\
from argendata_datasets import Datasets
from pathlib import Path

DATASETS_METADATA_PATH = Path(__file__).parent / 'datasets_metadata.json'
DATASETS_METADATA_PATH.write_text(Datasets.model_dump_json(indent=2))
"""

class Script(lamda.python.Script):
    known_sources = {
        **  ( GithubDependency('argendata_stan', 'joangq').as_source()
            | GithubDependency('argendata_datasets', 'joangq').as_source()
            | GithubDependency('argendata_api', 'argendatafundar', 'internal-api').as_source()
            )
    }

    def __post_init__(self):
        result = super().__post_init__()
        self.content += EXPORT_LINES
        return result
    
    @staticmethod
    def get_dependencies(content: str, **kwargs: object):
        known_sources = Script.known_sources.copy()
        external_sources = kwargs.get('known_sources') or {}
        known_sources.update(external_sources)
        analyzed_deps =  lamda.python.Script.get_dependencies(content, known_sources=known_sources)
        # TODO: Por algun motivo esto no esta funcinando correctamente,
        # y se añaden las dependencias de 'known_sources'.
        # queda parcheado asi por ahora, pero habria que cambiarlo.
        return list(set(analyzed_deps)|set(known_sources.values()))
