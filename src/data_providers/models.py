from typing import Union
from pydantic import BaseModel


class Quote(BaseModel):
    symbol: Union[str, None] = None
    price: Union[float, None] = None
    change: Union[float, None] = None
    change_pct: Union[float, None] = None
    volume: Union[int, None] = None
    timestamp_ts: Union[int, None] = None

    country_code: Union[str, None] = None
    logoid: Union[str, None] = None
    short_name: Union[str, None] = None
    pro_name: Union[str, None] = None
    currency_id: Union[str, None] = None
    type: Union[str, None] = None
    source_logoid: Union[str, None] = None
    description: Union[str, None] = None
    current_session: Union[str, None] = None

    logo_url: Union[str, None] = None
    source_logo_url: Union[str, None] = None
