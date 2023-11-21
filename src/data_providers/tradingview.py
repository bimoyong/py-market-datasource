from typing import List

import pandas as pd
import pytz

import tradingview as tv_lib
from data_providers.data_provider import DataProvider
from data_providers.enums import Adjustment
from data_providers.models import Quote
from tradingview import set_index_by_timestamp


class TradingView(DataProvider):
    _tv: tv_lib.TradingView = None
    username: str = ''
    password: str = ''
    token: str = ''
    market: str = ''

    @property
    def tv(self):
        if not self._tv:
            self._tv = tv_lib.TradingView(self.username,
                                          self.password,
                                          self.token,
                                          self.market)

        return self._tv

    def quote(self, symbol: str) -> Quote:
        quote = self._tv.current_quote(symbol)
        rst = Quote(**quote)

        return rst

    def ohlcv(self,
              symbols: str | List[str],
              interval: str,
              total_candle: int,
              charts: List[str] = None,
              adjustment=Adjustment.DIVIDENDS,
              tzinfo: pytz.BaseTzInfo = pytz.UTC) -> pd.DataFrame:
        if isinstance(symbols, str):
            symbols = [symbols]

        ohlcv_iter = self.tv.historical_multi_symbols(symbols,
                                                      interval,
                                                      total_candle,
                                                      charts,
                                                      adjustment.value)

        ohlcv_ts_index = map(lambda x: set_index_by_timestamp(x, tzinfo), ohlcv_iter)
        df = pd.concat(ohlcv_ts_index, axis=0, keys=symbols)
        df.index.names = ['symbol', 'timestamp']

        return df
