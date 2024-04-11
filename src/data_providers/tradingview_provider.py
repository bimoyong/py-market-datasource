from typing import Dict, List, Union

import pandas as pd
import pytz

from data_providers.data_provider import DataProvider
from data_providers.enums import Adjustment
from data_providers.models import BaseQuote, Quote
from tradingview import TradingView, set_index_by_timestamp


class TradingViewProvider(DataProvider):
    STORAGE_BASE_URL = 'https://s3-symbol-logo.tradingview.com'

    _tv: TradingView = None
    username: str = ''
    password: str = ''
    token: str = ''
    market: str = ''

    @property
    def tv(self) -> TradingView:
        if not self._tv:
            self._tv = TradingView(self.username,
                                   self.password,
                                   self.token,
                                   self.market)

        return self._tv

    def quotes(self,
               symbols: Union[str, List[str]],
               fields: List[str] = None) -> Union[Quote, Dict[str, Quote]]:
        return_single = isinstance(symbols, str)

        if fields is None:
            fields = [*Quote.model_fields.keys()]
        elif '*' in fields:
            fields = []

        fields = [Quote.fields_map().get(i, i) for i in fields or []]

        quotes = self.tv.current_quotes(symbols, fields=fields)

        if return_single:
            quotes = {symbols: quotes}

        rst: Dict[str, Quote] = {}
        for symbol, quote_dict in quotes.items():
            quote_dict.update({'symbol': symbol})

            extra = {k: v for k, v in quote_dict.items()
                     if k not in Quote.non_extra_keys()}
            if extra:
                quote_dict.update({'extra': extra})

            quote = Quote(**quote_dict)

            if quote.logoid:
                quote.logo_url = f'{__class__.STORAGE_BASE_URL}/{quote.logoid}--big.svg'

            if quote.source_logoid:
                quote.source_logo_url = f'{__class__.STORAGE_BASE_URL}/{quote.source_logoid}--big.svg'

            rst[symbol] = quote

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

        ohlcv_ts_index = map(lambda x: set_index_by_timestamp(x, tzinfo), ohlcv_iter)
        df = pd.concat(ohlcv_ts_index, axis=0, keys=symbols)
        df.index.names = ['symbol', 'timestamp']

        return df
