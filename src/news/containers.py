from dependency_injector import containers
from dependency_injector.providers import (AbstractSingleton, Configuration,
                                           Dict, Singleton)

from news.provider import NewsProvider, ProviderSelector
from news.seeking_alpha import SeekingAlpha


class Container(containers.DeclarativeContainer):
    config = Configuration(yaml_files=['config.yml'])

    client = AbstractSingleton(NewsProvider).add_attributes(
        WORKERS_NO=config.NEWS.WORKERS_NO,
        THROTTLING_SECONDS=config.NEWS.THROTTLING_SECONDS,
        DB_TABLE=config.NEWS.DB_TABLE,
    )

    source_selector = Singleton(ProviderSelector).add_attributes(
        sources=Dict({
            SeekingAlpha.__name__: Singleton(SeekingAlpha).add_attributes(
                WORKERS_NO=config.NEWS.SeekingAlpha.WORKERS_NO,
                THROTTLING_SECONDS=config.NEWS.SeekingAlpha.THROTTLING_SECONDS,
                BASE_URL=config.NEWS.SeekingAlpha.BASE_URL,
                DB_TABLE=config.NEWS.SeekingAlpha.DB_TABLE,
            ),
        }),
    )
