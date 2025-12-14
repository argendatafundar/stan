from pydantic import BaseModel, Field
from datetime import datetime as dt
from abc import ABC, abstractmethod
from ..utils import AbstractField

class Environment(BaseModel, ABC):
    dependencies: list[str] = Field(..., repr=True)
    checksum: str = AbstractField(
        ..., 
        description='The checksum of the environment.'
    )

    @abstractmethod
    def load(cls, path: str) -> 'Environment':
        ...

class FileBase(BaseModel, ABC):
    filename: str = Field(..., repr=True)
    contents: str = Field(..., repr=False)
    datetime: dt = Field(..., repr=True)

class ExecutionResult[A, B](BaseModel):
    process: A
    product: B

class Script[E: Environment](FileBase):
    environment: E = Field(default_factory=Environment)
    produces: list[str] = Field(
        ...,
        description='A list of datasets with filename and checksum that the script produces.',
        examples=[
            'R1C1(output.csv@1234567890)',
        ]
    )
    consumes: list[str] = AbstractField(
        ...,
        description='A list of datasets with version hashes that the script consumes.',
        examples=[
            'R1C0@1234567890',
        ]
    )

    @classmethod
    def load(cls, script_path: str, environment: E, produces: list[str], consumes: list[str]) -> 'Script':
        import pathlib
        script_path = pathlib.Path(script_path)
        filename = script_path.name
        contents = script_path.read_text()
        datetime = script_path.stat().st_mtime
        return cls(
            filename=filename, 
            contents=contents, 
            datetime=datetime, 
            environment=environment,
            produces=produces,
            consumes=consumes,
        )

    @abstractmethod
    def run(self) -> ExecutionResult:
        raise NotImplementedError('Subclasses must implement this method')