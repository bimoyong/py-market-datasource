from dependency_injector import containers, providers

from news.provider import NewsProvider


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    client = providers.AbstractSingleton(NewsProvider)
