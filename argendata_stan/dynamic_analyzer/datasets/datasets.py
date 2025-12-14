from ...common import ConfigFlags, AnalyzerFunc
import ast
from dataclasses import dataclass

@dataclass
class ExportedDataset:
    codigo: str
    filename: str
    metadata: dict

def _execute(tree: ast.Module, globals, locals):
    code = ast.unparse(tree)
    result = exec(code, globals, locals)
    return result, globals, locals

def execute(tree, globals=None, locals=None):
    globals = globals or {}
    locals = locals or {}
    return _execute(tree, globals, locals)

analyze_datasets: AnalyzerFunc[dict]
def analyze_datasets(text: str, config: ConfigFlags, result: dict):
    if not config.detect_output_datasets:
        return result
    
    from argendata_datasets.dsl.analyzer import get_dataset_registrations
    from argendata_datasets.dsl.datasets import DatasetProxy

    symbols = get_dataset_registrations(ast.parse(text))

    """
    [{'symbol': 'dataset', 'save': DatasetSave(symbol='dataset', node=<ast.Call object at 0x747ca632cfd0>), 'registration': DatasetRegister(symbol='dataset', name='R1C1', filename=Constant(value='output.csv'), stmt_index=2)}, {'symbol': 'another_dataset', 'save': DatasetSave(symbol='another_dataset', node=<ast.Call object at 0x747ca6322e90>), 'registration': DatasetRegister(symbol='another_dataset', name='R1C2', filename=Constant(value='another_output.csv'), stmt_index=4)}]
    """

    max_stmt_index = max(
        record["registration"].stmt_index for record in symbols
    )

    statements = ast.parse(text).body[:max_stmt_index+1]

    _, globals, locals = execute(statements)

    exported_datasets = []
    for record in symbols:
        symbol_value = globals.get(record["symbol"], None)
        if symbol_value is None:
            symbol_value = locals.get(record["symbol"], None)
        if symbol_value is None:
            raise RuntimeError(f'Symbol {record["symbol"]} not found.')
        if not isinstance(symbol_value, DatasetProxy):
            continue 
        metadata = symbol_value._get_registrations_metadata_stack()
        assert len(metadata) > 0
        exported_datasets.append(metadata.pop())

    if len(exported_datasets) == 0:
        raise RuntimeError(f'No datasets exported.')

    for i, exported_dataset in enumerate(exported_datasets):
        filename = exported_dataset.pop('filename')
        codigo = exported_dataset.pop('name')
        metadata = exported_dataset
        exported_datasets[i] = ExportedDataset(
            codigo=codigo, 
            filename=filename, 
            metadata=metadata
        )

    result["output_datasets"] = exported_datasets

    return result