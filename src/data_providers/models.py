from pydantic import BaseModel


class Quote(BaseModel):
    symbol: str | None = None
    price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    volume: int | None = None
    timestamp_ts: int | None = None
