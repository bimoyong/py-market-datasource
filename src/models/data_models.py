from typing import Any, Dict, Union

from pydantic import Field

from models.base_model import BaseModel


class BaseQuote(BaseModel):
    symbol: Union[str, None] = None
    price: Union[float, None] = Field(serialization_alias='price', alias='lp', default=None)
    change: Union[float, None] = Field(serialization_alias='change', alias='ch', default=None)
    change_pct: Union[float, None] = Field(serialization_alias='change_pct', alias='chp', default=None)
    volume: Union[int, None] = None
    timestamp_ts: Union[int, None] = Field(serialization_alias='timestamp_ts', alias='lp_time', default=None)


class Quote(BaseQuote):
    country_code: Union[str, None] = None
    logoid: Union[str, None] = None
    short_name: Union[str, None] = None
    pro_name: Union[str, None] = None
    currency_id: Union[str, None] = None
    type: Union[str, None] = None
    source_logoid: Union[str, None] = Field(serialization_alias='source_logoid', alias='source-logoid', default=None)
    description: Union[str, None] = None
    current_session: Union[str, None] = None

    logo_url: Union[str, None] = None
    source_logo_url: Union[str, None] = None

    change_5d: Union[float, None] = Field(serialization_alias='change_5d', alias='change_5d', default=None)
    change_5d_pct: Union[float, None] = Field(serialization_alias='change_5d_pct', alias='change_5d_pct', default=None)
    low_5d: Union[float, None] = Field(serialization_alias='low_5d', alias='low_5d', default=None)
    high_5d: Union[float, None] = Field(serialization_alias='high_5d', alias='high_5d', default=None)

    extra: Dict[str, Any] = None
