from typing import Dict, List, Union

import pandas as pd
import pytz

import tradingview as tv_lib
from data_providers.data_provider import DataProvider
from data_providers.enums import Adjustment
from data_providers.models import Quote


class TradingView(DataProvider):
    STORAGE_BASE_URL = 'https://s3-symbol-logo.tradingview.com'

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

    def quote(self, symbols: Union[str, List[str]]) -> Union[Quote, Dict[str, Quote]]:
        return_multi = isinstance(symbols, list)

        quotes = self.tv.current_quote(symbols)
        if not return_multi:
            quotes = {symbols: quotes}

        rst: Dict[str, Quote] = {}
        for k, v in quotes.items():
            q = Quote(**v)

            if q.logoid:
                q.logo_url = f'{__class__.STORAGE_BASE_URL}/{q.logoid}.svg'

            if q.source_logoid:
                q.source_logo_url = f'{__class__.STORAGE_BASE_URL}/{q.source_logo_url}.svg'

            rst[k] = q

        if return_multi:
            return rst

        return rst[symbols]

    def ohlcv(self,
              symbols: Union[str, List[str]],
              interval: str,
              total_candle: int,
              charts: List[str] = None,
              adjustment=Adjustment.DIVIDENDS,
              tzinfo: Union[str, pytz.BaseTzInfo] = pytz.UTC) -> pd.DataFrame:
        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(tzinfo, str):
            tzinfo = pytz.timezone(tzinfo)

        ohlcv_iter = self.tv.historical_multi_symbols(symbols,
                                                      interval,
                                                      total_candle,
                                                      charts,
                                                      adjustment.value)

        ohlcv_ts_index = map(lambda x: tv_lib.set_index_by_timestamp(x, tzinfo), ohlcv_iter)
        df = pd.concat(ohlcv_ts_index, axis=0, keys=symbols)
        df.index.names = ['symbol', 'timestamp']

        return df
