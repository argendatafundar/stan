from dataclasses import asdict, dataclass
from functools import reduce
from operator import or_ as union
from .flags import get_flags

CONFIG_TOKEN = "#%"
DATACLASS_CONFIG = dict(
    init         = True,
    repr         = True, 
    eq           = True, 
    order        = False,
    unsafe_hash  = False, 
    frozen       = True, 
    match_args   = True,
    kw_only      = True, 
    slots        = True, 
    weakref_slot = False,
)

@dataclass(**DATACLASS_CONFIG)
class ConfigFlags:
    # static analysis flags

    ## imports/dependencies
    detect_dependencies: bool = False
    parse_imports: bool = True
    parse_github_dependencies: bool = True
    parse_environment: bool = False

    ## input datasets
    detect_datasets: bool = False

    # dynamic analysis flags
    ## output datasets
    detect_output_datasets: bool = True

    def __post_init__(self):
        if self.detect_datasets:
            import argendata_datasets
    
    @classmethod
    def detect_from_text(cls, text: str):
        return detect_config_from_text(text)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, config: dict):
        return cls(**config)

def get_config(text: str):
    return get_flags(text, CONFIG_TOKEN)

def detect_config_from_text(text: str):
    detected_flags = get_config(text)
    detected_flags: set[str] = reduce(union, detected_flags.values(), set())
    
    config: dict[str, bool] = {
        flag: True
        for flag in ConfigFlags.__annotations__
        if flag in detected_flags
    }

    return config