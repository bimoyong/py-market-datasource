from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import AbstractSingleton, Configuration

from data_providers.data_provider import DataProvider


class Container(DeclarativeContainer):
    config = Configuration(yaml_files=['config.yml'])

    client = AbstractSingleton(DataProvider)
