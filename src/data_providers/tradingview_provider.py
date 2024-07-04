from datetime import datetime
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
    TOKEN: str = ''
    market: str = ''

    @property
    def tv(self) -> TradingView:
        if not self._tv:
            self._tv = TradingView(self.username,
                                   self.password,
                                   self.TOKEN,
                                   self.market,
                                   self.WORKERS_NO)

        return self._tv

    def search(self,
               symbols: List[str],
               params: Dict[str, Any] = None) -> Dict[str, Union[None, Dict[str, Any]]]:
        if params is None:
            params = {}

        rst = self.tv.search_multi(queries=symbols, params=params)

        return rst

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
        def _get_ohclv(ohclv: pd.DataFrame) -> pd.DataFrame:
            if ohclv is None:
                ohclv = self.ohclv(rst.keys(),
                                   freq='1D',
                                   total_candles=252).reset_index()
            return ohclv

        if set(fields) & set(['change_5d', 'change_5d_pct', 'low_5d', 'high_5d']):
            ohclv = _get_ohclv(ohclv)
            perf_dict = self.calc_perf(ohclv, '5D')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update={_k: _v for _k, _v in v.items() if _k in fields})

        if set(fields) & set(['change_1m', 'change_1m_pct', 'low_1m', 'high_1m']):
            ohclv = _get_ohclv(ohclv)
            perf_dict = self.calc_perf(ohclv, '1M')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update={_k: _v for _k, _v in v.items() if _k in fields})

        if set(fields) & set(['change_mtd', 'change_mtd_pct', 'low_mtd', 'high_mtd']):
            ohclv = _get_ohclv(ohclv)
            perf_dict = self.calc_perf(ohclv, 'MTD')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update={_k: _v for _k, _v in v.items() if _k in fields})

        if set(fields) & set(['change_ytd', 'change_ytd_pct', 'low_ytd', 'high_ytd']):
            ohclv = _get_ohclv(ohclv)
            perf_dict = self.calc_perf(ohclv, 'YTD')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update=v)

        if return_single:
            return rst[symbols]

        return rst

    def ohclv(self,
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

        ohclv = self.tv.historical_multi_symbols(symbols=symbols,
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

        ohclv = set_index_by_timestamp(ohclv, tzinfo)

        ohclv.index.name = cols_map.get(ohclv.index.name, ohclv.index.name)
        ohclv.columns = [cols_map.get(c, c) for c in ohclv.columns]

        ohclv = ohclv \
            .drop(['timestamp_ts'], axis=1, errors='ignore') \
            .reset_index().set_index(['Date', 'Symbol'])

        return ohclv

    def economic_calendar(self,
                          from_date: Union[str, datetime],
                          to_date: Union[str, datetime],
                          countries: List[str] = None,
                          fetch_related_events=False) -> List[Dict[str, Any]]:
        if isinstance(from_date, datetime):
            from_date = from_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        if isinstance(to_date, datetime):
            to_date = to_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        if countries is None:
            countries = ['US']

        rst = self.tv.economic_calendar(from_date,
                                        to_date,
                                        countries,
                                        fetch_related_events)

        return rst

    def calc_perf(self,
                  ohclv: pd.DataFrame,
                  freq: str = '5d') -> Dict[str, Dict[str, Any]]:
        symbols = ohclv.Symbol.unique()
        _ohclv: pd.DataFrame = ohclv.set_index(['Date', 'Symbol'])

        freq = freq.lower()
        freq_mapper = {
            '5d': 5,
            '1m': 21,
            'mtd': 'M',
            'ytd': 'Y',
        }
        freq_num: Union[int, str] = freq_mapper.get(freq, freq)

        perf_dict = {}
        for s in symbols:
            _ohclv_sym: pd.DataFrame = _ohclv.loc[:, s, :].copy()

            if isinstance(freq_num, str):
                _ohclv_agg: pd.DataFrame = _ohclv_sym.Close.groupby(_ohclv_sym.index.to_period(freq_num)).last().rename('close').to_frame()
                _ohclv_agg.loc[:, f'close_{freq}_prev'] = _ohclv_agg.close.shift(1)
                _ohclv_agg.loc[:, f'change_{freq}'] = _ohclv_agg.close - _ohclv_agg[f'close_{freq}_prev']
                _ohclv_agg.loc[:, f'change_{freq}_pct'] = _ohclv_agg[f'change_{freq}'] / _ohclv_agg[f'close_{freq}_prev']
                _ohclv_agg.loc[:, f'low_{freq}'] = _ohclv_sym.Low.groupby(_ohclv_sym.index.to_period(freq_num)).min()
                _ohclv_agg.loc[:, f'high_{freq}'] = _ohclv_sym.High.groupby(_ohclv_sym.index.to_period(freq_num)).max()
                _ohclv_sym = _ohclv_agg

            elif isinstance(freq_num, int):
                _ohclv_sym.rename({'Close': 'close'}, axis=1, inplace=True)
                _ohclv_sym.loc[:, f'close_{freq}_prev'] = _ohclv_sym.close.shift(freq_num)
                _ohclv_sym.loc[:, f'change_{freq}'] = _ohclv_sym.close - _ohclv_sym[f'close_{freq}_prev']
                _ohclv_sym.loc[:, f'change_{freq}_pct'] = _ohclv_sym[f'change_{freq}'] / _ohclv_sym[f'close_{freq}_prev']
                _ohclv_sym.loc[:, f'low_{freq}'] = _ohclv_sym.Low.rolling(freq_num).min()
                _ohclv_sym.loc[:, f'high_{freq}'] = _ohclv_sym.High.rolling(freq_num).max()

            cols_included = ['close',
                             f'change_{freq}',
                             f'change_{freq}_pct',
                             f'low_{freq}',
                             f'high_{freq}']

            perf_dict[s] = _ohclv_sym[cols_included].iloc[-1].to_dict()

        return perf_dict
