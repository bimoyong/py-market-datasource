"""Endpoints module."""

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse

from models.news_enums import Category
from models.news_model import MasterData, Paging
from news import API_VERSION
from news.containers import Container
from news.provider import NewsProvider, ProviderSelector

router = APIRouter(prefix=f'/{API_VERSION}/news')


@inject
async def validate_source(source: str = Query(None),
                          selector: ProviderSelector = Depends(Provide[Container.source_selector])):
    if source is not None and source not in selector.sources:
        raise RequestValidationError(f'Source "{source}" not found')

    return source


@router.get('/master',
            response_model=MasterData,
            response_model_exclude_none=True)
@inject
async def master(provider: NewsProvider = Depends(Provide[Container.client]),
                 selector: ProviderSelector = Depends(Provide[Container.source_selector])):
    resp = provider.master_data()
    resp.sources = [i for i in selector.sources.keys()]

    return resp


@router.get('/crawl',
            response_model=Paging,
            response_model_exclude_none=True)
@inject
async def crawl(source: str = Query(None),
                category: Category = Query(Category.FINANCIAL),
                from_date: datetime = Query(None),
                to_date: datetime = Query(None),
                items_per_page: int = Query(40),
                selector: ProviderSelector = Depends(Provide[Container.source_selector])):
    provider = selector.sources[source]

    resp = provider.crawl(category=category,
                          from_date=from_date,
                          to_date=to_date,
                          items_per_page=items_per_page)

    return resp


@router.get('/list',
            response_model=Paging,
            response_model_exclude_none=True)
@inject
async def list(source: str = Depends(validate_source),
               category: Category = Query(None),
               from_date: datetime = Query(None),
               to_date: datetime = Query(None),
               items_per_page: int = Query(40),
               page_number: int = Query(1),
               selector: ProviderSelector = Depends(Provide[Container.source_selector])):
    provider = selector.sources[source]

    resp = provider.list(category=category,
                         from_date=from_date,
                         to_date=to_date,
                         items_per_page=items_per_page,
                         page_number=page_number)

    return resp


@router.get('/detail',
            response_model_exclude_none=True)
@inject
async def detail(source: str = Query(None),
                 url: str = Query(None),
                 return_html: bool = Query(True),
                 selector: ProviderSelector = Depends(Provide[Container.source_selector])):
    provider = selector.sources[source]

    html = provider.detail(url=url, return_html=return_html)

    resp = HTMLResponse(content=html, status_code=200)

    return resp
