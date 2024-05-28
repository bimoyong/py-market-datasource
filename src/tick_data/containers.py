from dependency_injector import containers
from dependency_injector.providers import AbstractSingleton, Configuration

from tick_data.provider import TickDataProvider


class Container(containers.DeclarativeContainer):
    config = Configuration(yaml_files=['config.yml'])

    client = AbstractSingleton(TickDataProvider)
