from typing import Union
from pydantic import BaseModel


class Quote(BaseModel):
    symbol: Union[str, None] = None
    price: Union[float, None] = None
    change: Union[float, None] = None
    change_pct: Union[float, None] = None
    volume: Union[int, None] = None
    timestamp_ts: Union[int, None] = None
