"""Endpoints module."""

from typing import Any, Dict, List, Union

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError

from data_providers import API_VERSION
from data_providers.containers import Container
from data_providers.data_provider import DataProvider
from models.data_models import Quote

router = APIRouter(prefix=f'/{API_VERSION}/data')


@router.get('/search',
            response_model=Dict[str, Union[None, Dict[str, Any]]],
            response_model_exclude_none=True)
@inject
async def search(
    symbols: List[str] = Query(None),
    country: str = Query('US'),
    exchange: str = Query(None),
    search_type: str = Query(None),
    economic_category: str = Query(None),
    start: int = Query(0),
    service: DataProvider = Depends(Provide[Container.client]),
):
    if not symbols:
        raise RequestValidationError('"symbols" query is required')

    params = {
        'country': country,
        'exchange': exchange,
        'search_type': search_type,
        'economic_category': economic_category,
        'start': start,
    }
    resp = service.search(symbols=symbols, params=params)

    return resp


@router.get('/quotes',
            response_model=Union[Quote, Dict[str, Quote]],
            response_model_exclude_none=True)
@inject
async def quotes(
    symbols: List[str] = Query(None),
    fields: List[str] = Query(None),
    service: DataProvider = Depends(Provide[Container.client]),
):
    if not symbols:
        raise RequestValidationError('"symbols" query is required')

    resp = service.quotes(symbols=symbols, fields=fields)

    return resp


@router.get('/economic_calendar',
            response_model=List[Dict[str, Any]],
            response_model_exclude_none=True)
@inject
async def economic_calendar(
    from_date: str = Query(None),
    to_date: str = Query(None),
    countries: List[str] = Query(None),
    fetch_related_events: bool = Query(False),
    service: DataProvider = Depends(Provide[Container.client]),
):
    resp = service.economic_calendar(from_date=from_date,
                                     to_date=to_date,
                                     countries=countries,
                                     fetch_related_events=fetch_related_events)

    return resp
