from pydantic import BaseModel


class Quote(BaseModel):
    symbol: str
    price: float
    change: float
    change_pct: float
    volume: int
    timestamp_ts: int
