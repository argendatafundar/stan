from .common import ConfigFlags, detect_config_from_text

from . import dependencies, datasets

class StaticAnalyzer:
    config: ConfigFlags

    def __init__(self, config: None|ConfigFlags=None, **kwargs):
        self.config = config or ConfigFlags(**kwargs)

    def detect_config(self, code: str, config: None|ConfigFlags=None):
        config = config or self.config
        detected_config = detect_config_from_text(code)

        config = ConfigFlags.from_dict(
            config.to_dict() | detected_config
        )

        return config
    
    def run(self, code: str, detect_config: bool = True):
        result = dict()

        config = self.config
        if detect_config:
            config = self.detect_config(code, config)
        
        result = dependencies.analyze(code, config, result)
        result = datasets.analyze(code, config, result)

        return result
    
