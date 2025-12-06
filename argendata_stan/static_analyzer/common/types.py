from .config_flags import ConfigFlags
from typing import Callable, MutableMapping

type Analyzer[T: MutableMapping] = Callable[[str, ConfigFlags, T], T]