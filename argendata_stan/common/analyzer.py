from ..common import ConfigFlags, detect_config_from_text
from abc import ABC, abstractmethod

class Analyzer(ABC):
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

    @abstractmethod
    def run(self, code: str, detect_config: bool = True) -> dict:
        ...