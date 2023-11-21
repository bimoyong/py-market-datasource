from dependency_injector import containers, providers

from data_providers.data_providers import DataProvider


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    client = providers.AbstractSingleton(DataProvider)
