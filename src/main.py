import logging as logger
from logging import INFO

from dependency_injector import providers
from fastapi import FastAPI
from google.cloud.logging import Client as LoggingClient

from data_providers import endpoints
from data_providers.containers import Container
from data_providers.tradingview_provider import TradingViewProvider

client = LoggingClient()
client.setup_logging(log_level=INFO)


def create_app() -> FastAPI:
    container = Container()
    container.client.override(providers.Singleton(TradingViewProvider))

    _app = FastAPI()
    _app.container = container
    _app.include_router(endpoints.router)
    return _app


app = create_app()


@app.get('/healthz')
async def healthz():
    return 'ok'
