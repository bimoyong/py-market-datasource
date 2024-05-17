"""Endpoints module."""

from datetime import datetime
from typing import List, Union

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from models.news_enums import Category
from models.news_model import MasterData, News, Paging
from news import API_VERSION
from news.containers import Container
from news.provider import NewsProvider

router = APIRouter(prefix=f'/{API_VERSION}/news')


@router.get('/master',
            response_model=MasterData,
            response_model_exclude_none=True)
@inject
async def master(provider: NewsProvider = Depends(Provide[Container.client])):
    resp = provider.master_data()

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
                provider: NewsProvider = Depends(Provide[Container.client])):

    resp = provider.crawl(category=category,
                          from_date=from_date,
                          to_date=to_date,
                          items_per_page=items_per_page)

    return resp


@router.get('/list',
            response_model=Paging,
            response_model_exclude_none=True)
@inject
async def list(source: str = Query(None),
               category: Category = Query(None),
               from_date: datetime = Query(None),
               to_date: datetime = Query(None),
               items_per_page: int = Query(40),
               page_number: int = Query(1),
               provider: NewsProvider = Depends(Provide[Container.client])):

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
                 provider: NewsProvider = Depends(Provide[Container.client])):

    html = provider.detail(url=url, return_html=return_html)

    resp = HTMLResponse(content=html, status_code=200)

    return resp
