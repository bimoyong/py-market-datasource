from dependency_injector import containers, providers

from data_providers.data_provider import DataProvider


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=['.endpoints'])

    config = providers.Configuration()

    client = providers.AbstractSingleton(DataProvider)
