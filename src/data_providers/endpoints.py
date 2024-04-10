"""Endpoints module."""

from typing import Dict, List, Union

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError

from data_providers import DataProvider
from data_providers.containers import Container
from data_providers.models import Quote

router = APIRouter()


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
