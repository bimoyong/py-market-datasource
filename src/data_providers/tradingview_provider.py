from typing import Any, Dict, List, Union

import pandas as pd
import pytz

from data_providers.data_provider import DataProvider
from data_providers.enums import Adjustment
from models.data_models import Quote
from tradingview import TradingView, set_index_by_timestamp


class TradingViewProvider(DataProvider):
    STORAGE_BASE_URL = 'https://s3-symbol-logo.tradingview.com'

    _tv: TradingView = None
    username: str = ''
    password: str = ''
    token: str = ''
    market: str = ''
    workers_no: int = 1

    @property
    def tv(self) -> TradingView:
        if not self._tv:
            self._tv = TradingView(self.username,
                                   self.password,
                                   self.token,
                                   self.market,
                                   self.WORKERS_NO)

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

        ohclv: pd.DataFrame = None

        if set(fields) & set(['change_5d', 'change_5d_pct', 'low_5d', 'high_5d']):
            ohclv = self.tv.historical_multi_symbols(rst.keys(),
                                                     interval='1D',
                                                     total_candle=10)

            perf_dict = self.calc_perf(ohclv, '5D')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update=v)

        if return_single:
            return rst[symbols]

        return rst

    def ohlcv(self,
              symbols: Union[str, List[str]],
              freq: str,
              total_candles: int,
              charts: List[str] = None,
              adjustment=Adjustment.DIVIDENDS,
              tzinfo: Union[str, pytz.BaseTzInfo] = pytz.UTC) -> pd.DataFrame:
        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(tzinfo, str):
            tzinfo = pytz.timezone(tzinfo)

        total_candles += 1  # preserve 1 bar because TradingView returns less than 1 bar

        ohlcv = self.tv.historical_multi_symbols(symbols=symbols,
                                                 interval=freq,
                                                 total_candle=total_candles,
                                                 charts=charts,
                                                 adjustment=adjustment.value)

        cols_map = {
            'timestamp': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
        }

        ohlcv = set_index_by_timestamp(ohlcv, tzinfo)

        ohlcv.index.name = cols_map.get(ohlcv.index.name, ohlcv.index.name)
        ohlcv.columns = [cols_map.get(c, c) for c in ohlcv.columns]

        ohlcv = ohlcv \
            .drop(['timestamp_ts'], axis=1, errors='ignore') \
            .reset_index().set_index(['Date', 'Symbol'])

        return ohlcv
    
    def calc_perf(self,
                  ohclv: pd.DataFrame,
                  interval: str = '5d') -> Dict[str, Dict[str, Any]]:
        symbols = ohclv.Symbol.unique()
        _ohclv = ohclv.set_index(['Symbol', 'timestamp_ts'])

        interval = interval.lower()
        interval_mapper = {
            '5d': 5,
        }
        interval_num: int = interval_mapper.get(interval, interval)

        for s in symbols:
            _ohclv.loc[[s], f'change_{interval}'] = _ohclv.loc[[s]].close - _ohclv.loc[[s]].close.shift(interval_num)
            _ohclv.loc[[s], f'change_{interval}_pct'] = _ohclv.loc[[s], f'change_{interval}'] / _ohclv.loc[[s]].close.shift(interval_num)
            _ohclv.loc[[s], f'low_{interval}'] = _ohclv.loc[[s]].low.rolling(interval_num).min()
            _ohclv.loc[[s], f'high_{interval}'] = _ohclv.loc[[s]].high.rolling(interval_num).max()

        cols_included = ['close',
                         f'change_{interval}',
                         f'change_{interval}_pct',
                         f'low_{interval}',
                         f'high_{interval}']

        perf_dict = _ohclv.groupby('Symbol').last()[cols_included].to_dict('index')

        return perf_dict
