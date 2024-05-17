import logging as logger
from logging import INFO

from dependency_injector.providers import Singleton
from fastapi import FastAPI
from google.cloud.logging import Client as LoggingClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from data_providers.containers import Container as DataContainerV1
from data_providers.endpoints import router as data_endpoints
from data_providers.tradingview_provider import TradingViewProvider
from news.containers import Container as NewsContainerV1
from news.endpoints import router as news_endpoints
from news.seeking_alpha import SeekingAlpha

client = LoggingClient()
client.setup_logging(log_level=INFO)


def create_app() -> FastAPI:
    data_container_v1 = DataContainerV1()
    data_container_v1.wire(packages=['data_providers'])
    data_container_v1.client.override(Singleton(TradingViewProvider))

    new_container_v1 = NewsContainerV1()
    new_container_v1.wire(packages=['news'])
    new_container_v1.client.override(Singleton(SeekingAlpha))

    _app = FastAPI()
    _app.container = new_container_v1
    _app.new_container_v1 = new_container_v1
    _app.include_router(data_endpoints)
    _app.include_router(news_endpoints)
    return _app


app = create_app()


@app.get('/healthz')
async def healthz():
    return 'ok'


@app.exception_handler(ConnectionRefusedError)
async def value_error_exception_handler(request: Request, exc: ConnectionRefusedError):
    return JSONResponse(
        status_code=400,
        content={'message': str(exc)},
    )
