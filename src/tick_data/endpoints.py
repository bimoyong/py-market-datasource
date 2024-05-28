"""Endpoints module."""

from typing import Annotated
from datetime import datetime
from typing import Any, List, Union
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse

from tick_data import API_VERSION
from tick_data.containers import Container
from tick_data.provider import TickDataProvider

router = APIRouter(prefix=f'/{API_VERSION}/tick_data')


@router.get('/list_files',
            response_model=Any,
            response_model_exclude_none=True)
@inject
async def list_files(from_date: datetime = Query(None),
                     to_date: datetime = Query(None),
                     provider: TickDataProvider = Depends(Provide[Container.client])):
    downloads = provider.list_files(from_date=from_date,
                                    to_date=to_date)
    downloads.reset_index(inplace=True)

    return downloads.to_dict(orient='records')


@router.get('/download_files_background',
            response_model=Any,
            response_model_exclude_none=True)
@inject
async def download_file(workers_no: int = Query(default=4),
                        provider: TickDataProvider = Depends(Provide[Container.client])):
    resp = provider.download_files_background(workers_no=workers_no)

    return resp

@router.get('/download_file',
            response_model=Any,
            response_model_exclude_none=True)
@inject
async def download_file(filenames: Annotated[List[str] | str, Query()],
                        force: bool = Query(default=False),
                        provider: TickDataProvider = Depends(Provide[Container.client])):
    resp = provider.download_file(filenames=filenames, force=force)

    return resp
