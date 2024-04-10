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

    def quotes(self,
               symbols: Union[str, List[str]],
               fields: Union[str, List[str]]) -> Union[Quote, Dict[str, Quote]]:
        return_single = isinstance(symbols, str)

        if fields is None:
            fields = ['lp', 'ch', 'chp', 'volume', 'lp_time',
                      'country_code', 'logoid', 'short_name', 'pro_name', 'currency_id', 'type', 'source-logoid', 'description', 'current_session']

        quotes = self.tv.current_quotes(symbols, fields=fields)

        if return_single:
            quotes = {symbols: quotes}

        rst: Dict[str, Quote] = {}
        for k, v in quotes.items():
            v.update({'symbol': k,
                      'price': v.get('lp', 0.0),
                      'change': v.get('ch', 0.0),
                      'change_pct': v.get('chp', 0.0),
                      'volume': v.get('volume', 0),
                      'timestamp_ts': v.get('lp_time', 0),
                      'source_logoid': v.get('source-logoid')})

            v = {k: v for k, v in v.items() if v is not None}

            q = Quote(**v)

            if q.logoid:
                q.logo_url = f'{__class__.STORAGE_BASE_URL}/{q.logoid}--big.svg'

            if q.source_logoid:
                q.source_logo_url = f'{__class__.STORAGE_BASE_URL}/{q.source_logoid}--big.svg'

            rst[k] = q

        if return_single:
            return rst[symbols]

        return rst

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
