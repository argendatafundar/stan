import rootdir
from argendata_stan import StaticAnalyzer, ConfigFlags

def test_detect_config():
    analyzer = StaticAnalyzer()

    config = analyzer.detect_config(
        r"""
        #% detect_dependencies, detect_datasets
        """
    )

    assert config.detect_dependencies
    assert config.detect_datasets

    config = analyzer.detect_config(
        r"""
        #% detect_dependencies
        """
    )

    assert config.detect_dependencies
    assert not config.detect_datasets

    config = analyzer.detect_config(
        r"""
        #% detect_datasets
        """
    )

    assert not config.detect_dependencies
    assert config.detect_datasets

    # ==========================================================================

    analyzer = StaticAnalyzer(detect_datasets=True)
    config = analyzer.detect_config(
        r"""
        #% detect_datasets
        """
    )

    assert True == config.detect_datasets

    config = analyzer.detect_config("")
    assert True == config.detect_datasets

    config = analyzer.detect_config(
        r"""
        #% detect_datasets, detect_dependencies
        """
    )

    assert True == config.detect_datasets
    assert True == config.detect_dependencies

    config = analyzer.detect_config(
        r"""
        #% detect_dependencies
        """
    )

    assert True == config.detect_dependencies
    assert True == config.detect_datasets

    # ==========================================================================

    analyzer = StaticAnalyzer(detect_dependencies=True, detect_datasets=True)

    config = analyzer.detect_config("")
    assert True == config.detect_dependencies
    assert True == config.detect_datasets

    config = analyzer.detect_config(
        r"""
        #% detect_dependencies, detect_datasets
        """
    )

    assert True == config.detect_dependencies
    assert True == config.detect_datasets

    config = analyzer.detect_config(
        r"""
        #% detect_dependencies
        """
    )

    assert True == config.detect_dependencies
    assert True == config.detect_datasets

    config = analyzer.detect_config(
        r"""
        #% detect_datasets
        """
    )

    assert True == config.detect_dependencies
    assert True == config.detect_datasets

def test_configurations():
    assert (
        StaticAnalyzer(detect_dependencies=True, detect_datasets=True).config ==
        StaticAnalyzer(ConfigFlags(detect_dependencies=True, detect_datasets=True)).config
    )

    assert (
        StaticAnalyzer(detect_dependencies=True).config ==
        StaticAnalyzer(ConfigFlags(detect_dependencies=True)).config ==
        StaticAnalyzer(ConfigFlags(detect_dependencies=True, detect_datasets=False)).config
    )

    assert (StaticAnalyzer().config == ConfigFlags())

def test_run():
    analyzer = StaticAnalyzer(detect_datasets=True, detect_dependencies=True)
    result = analyzer.run(
"""
import pandas as pd
from sklearn.datasets import load_iris
"""
    )

    assert 'datasets' in result
    assert 'dependencies' in result

    assert 0 == len(result['datasets'])
    assert 'pandas' in result['dependencies']
    assert 'sklearn' in result['dependencies']

    result = analyzer.run(
r"""
import pandas as pd #' +pyarrow
"""
    )

    assert 2 == len(result['dependencies'])
    assert 'pandas' in result['dependencies']
    assert 'pyarrow' in result['dependencies']
    
    result = analyzer.run(
r"""
import pypdf #' pymupdf
"""
    )

    assert 1 == len(result['dependencies'])
    assert 'pymupdf' in result['dependencies']
    assert 'pypdf' not in result['dependencies']

    result = analyzer.run(
"""
import pypdf #' pymupdf,+rich
"""
    )

    assert 2 == len(result['dependencies'])
    assert 'pymupdf' in result['dependencies']
    assert 'rich' in result['dependencies']

    result = analyzer.run(
"""
import argendata_datasets #@ git+https://github.com/argendatafundar/datasets.git
"""
    )

    assert 1 == len(result['dependencies'])
    assert 'argendata_datasets@git+https://github.com/argendatafundar/datasets.git' in result['dependencies']
    assert 'argendata_datasets' not in result['dependencies']

    result = analyzer.run(
"""
import pandas as pd
import argendata_datasets #@ git+https://github.com/argendatafundar/datasets.git
"""
    )

    assert 2 == len(result['dependencies'])
    assert 'pandas' in result['dependencies']
    assert 'argendata_datasets@git+https://github.com/argendatafundar/datasets.git' in result['dependencies']
    assert 'argendata_datasets' not in result['dependencies']
    assert 'datasets' not in result['dependencies']

    result = analyzer.run(
"""
import argendata_datasets #@ git+ssh://git@github.com/argendatafundar/datasets.git
"""
    )

    assert 1 == len(result['dependencies'])
    assert 'argendata_datasets@git+ssh://git@github.com/argendatafundar/datasets.git' in result['dependencies']
    assert 'argendata_datasets' not in result['dependencies']
    assert 'datasets' not in result['dependencies']

    # ==========================================================================

    analyzer = StaticAnalyzer(detect_datasets=True)

    result = analyzer.run(
"""
import pandas as pd
from sklearn.datasets import load_iris
"""
    )

    assert 'datasets' in result
    assert 'dependencies' not in result

    assert 0 == len(result['datasets'])

    result = analyzer.run(
"""
from argendata_datasets.datasets import Datasets

x = Datasets.R1C0.get(version='latest')
"""
    )

    assert 'datasets' in result
    assert 'dependencies' not in result

    assert 1 == len(result['datasets'])

    datasets = result['datasets']
    assert datasets[0].name == 'R1C0'
    assert datasets[0].version == 'latest'

    result = analyzer.run(
"""
from argendata_datasets import Datasets
"""
    )

    assert 'datasets' in result
    assert 'dependencies' not in result

    assert 0 == len(result['datasets'])


def test_known_sources():
    config = ConfigFlags(
        detect_dependencies=True,
        known_sources={
        'argendata_datasets': 'argendata_datasets@git+https://github.com/argendatafundar/datasets.git'
    })
    analyzer = StaticAnalyzer(config)

    result = analyzer.run(
"""
import argendata_datasets
"""
    )

    assert 1 == len(result['dependencies'])
    assert 'argendata_datasets@git+https://github.com/argendatafundar/datasets.git' in result['dependencies']
    assert 'argendata_datasets' not in result['dependencies']
    assert 'datasets' not in result['dependencies']

    config = ConfigFlags(
        detect_dependencies=True,
    )

    analyzer = StaticAnalyzer(config)
    result = analyzer.run(
"""
import argendata_datasets
"""
    )

    assert 1 == len(result['dependencies'])
    assert 'argendata_datasets@git+https://github.com/argendatafundar/datasets.git' not in result['dependencies']
    assert 'argendata_datasets' in result['dependencies']
    assert 'datasets' not in result['dependencies']