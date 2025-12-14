from ..common import Analyzer, ConfigFlags
from warnings import deprecated
from . import datasets

@deprecated("Deprecated class")
class DynamicAnalyzer(Analyzer):
    config: ConfigFlags

    def run(self, code: str, detect_config: bool = True):
        result = dict()
        config = self.config
        if detect_config:
            config = self.detect_config(code, config)

        result = datasets.analyze(code, config, result)

        return result
