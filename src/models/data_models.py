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

    change_1m: Union[float, None] = Field(serialization_alias='change_1m', alias='change_1m', default=None)
    change_1m_pct: Union[float, None] = Field(serialization_alias='change_1m_pct', alias='change_1m_pct', default=None)
    low_1m: Union[float, None] = Field(serialization_alias='low_1m', alias='low_1m', default=None)
    high_1m: Union[float, None] = Field(serialization_alias='high_1m', alias='high_1m', default=None)

    change_mtd: Union[float, None] = Field(serialization_alias='change_mtd', alias='change_mtd', default=None)
    change_mtd_pct: Union[float, None] = Field(serialization_alias='change_mtd_pct', alias='change_mtd_pct', default=None)
    low_mtd: Union[float, None] = Field(serialization_alias='low_mtd', alias='low_mtd', default=None)
    high_mtd: Union[float, None] = Field(serialization_alias='high_mtd', alias='high_mtd', default=None)

    change_ytd: Union[float, None] = Field(serialization_alias='change_ytd', alias='change_ytd', default=None)
    change_ytd_pct: Union[float, None] = Field(serialization_alias='change_ytd_pct', alias='change_ytd_pct', default=None)
    low_ytd: Union[float, None] = Field(serialization_alias='low_ytd', alias='low_ytd', default=None)
    high_ytd: Union[float, None] = Field(serialization_alias='high_ytd', alias='high_ytd', default=None)

    extra: Dict[str, Any] = None
