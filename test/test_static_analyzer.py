import rootdir
from stan.static_analyzer.static_analyzer import (
    StaticAnalyzer,
    ConfigFlags,
    detect_config
)

def test_detect_config():
    config = detect_config(
        """
        #% parse_imports, parse_datasets
        """
    )

    assert config.parse_imports
    assert config.parse_datasets

    config = detect_config(
        """
        #% parse_imports
        """
    )

    assert config.parse_imports
    assert not config.parse_datasets

    config = detect_config(
        """
        #% parse_datasets
        """
    )

    assert not config.parse_imports
    assert config.parse_datasets