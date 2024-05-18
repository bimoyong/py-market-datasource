from typing import Any, List, Union
from datetime import datetime
from pydantic import Field

from models.base_model import BaseModel


class MasterData(BaseModel):
    sources: Union[List[str], None] = None
    categories: Union[List[str], None] = None


class News(BaseModel):
    source: Union[str, None] = Field(serialization_alias='source', alias='source', default=None)
    source_id: Union[str, None] = Field(serialization_alias='source_id', alias='source_id', default=None)
    timestamp: Union[str, None] = Field(serialization_alias='timestamp', alias='timestamp', default=None)
    timestamp_ts: Union[int, None] = Field(serialization_alias='timestamp_ts', alias='timestamp_ts', default=None)
    title: Union[str, None] = Field(serialization_alias='title', alias='title', default=None)
    description: Union[str, None] = Field(serialization_alias='description', alias='description', default=None)
    html: Union[str, None] = Field(serialization_alias='html', alias='html', default=None)
    text: Union[str, None] = Field(serialization_alias='text', alias='text', default=None)
    author: Union[str, None] = Field(serialization_alias='author', alias='author', default=None)
    link: Union[str, None] = Field(serialization_alias='link', alias='link', default=None)


class PagingMetadata(BaseModel):
    size: Union[int, None] = Field(serialization_alias='size', alias='size', default=None)
    total_pages: Union[int, None] = Field(serialization_alias='total_pages', alias='total_pages', default=None)
    total: Union[int, None] = Field(serialization_alias='total', alias='total', default=None)
    timestamp_min: Union[datetime, None] = Field(serialization_alias='timestamp_min', alias='timestamp_min', default=None)
    timestamp_max: Union[datetime, None] = Field(serialization_alias='timestamp_max', alias='timestamp_max', default=None)


class Paging(BaseModel):
    data: Union[List[Any]] = Field(serialization_alias='data', alias='data', default=[])
    metadata: Union[PagingMetadata] = Field(serialization_alias='metadata', alias='metadata', default=None)
