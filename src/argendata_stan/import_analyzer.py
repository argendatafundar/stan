from lamedh import PythonScript
from dataclasses import dataclass, field

@dataclass
class ExternalDependency:
    package: str
    url: str

    def __str__(self):
        return f'{self.package}@{self.url}'

@dataclass
class GithubDependency(ExternalDependency):
    package: str
    owner: str
    repo: None|str = None
    url: str = field(init=False)

    def __post_init__(self):
        self.url = f'git+https://github.com/{self.owner}/{self.repo}.git'

known_sources = {
    'argendata_stan': GithubDependency('argendata_stan', 'joangq')
}