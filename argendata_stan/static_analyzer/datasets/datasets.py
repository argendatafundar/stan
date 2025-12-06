from ..common import ConfigFlags, Analyzer

analyze_datasets: Analyzer[dict]
def analyze_datasets(text: str, config: ConfigFlags, result: dict):
    if not config.detect_datasets:
        return result
    
    from argendata_datasets.dsl.analyzer import get_datasets
    datasets = get_datasets(text)
    datasets = list(datasets)
    result["datasets"] = datasets

    return result