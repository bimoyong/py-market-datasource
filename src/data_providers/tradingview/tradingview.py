from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import pytz
from pydantic.v1.utils import deep_update
from tenacity import retry, stop_after_attempt, wait_exponential

from data_providers.data_provider import DataProvider
from data_providers.enums import Adjustment
from data_providers.tradingview.datetime import set_index_by_timestamp
from data_providers.tradingview.tradingview_client import TradingViewClient
from models.data_models import Quote


class TradingView(DataProvider):
    STORAGE_BASE_URL = 'https://s3-symbol-logo.tradingview.com'

    _tv: Optional[TradingViewClient] = None
    _executor: Optional[ThreadPoolExecutor] = None
    username: str = ''
    password: str = ''
    TOKEN: str = ''
    market: str = ''

    @property
    def tv(self) -> TradingViewClient:
        if not self._tv:
            self._tv = TradingViewClient(self.username, self.password, self.TOKEN, self.market)

        return self._tv

    @property
    def executor(self) -> ThreadPoolExecutor:
        if not self._executor:
            self._executor = ThreadPoolExecutor(max_workers=self.WORKERS_NO or 1)

        return self._executor

    def search(self,
               symbols: List[str],
               params: Dict[str, Any] = None) -> Dict[str, Union[None, Dict[str, Any]]]:
        if params is None:
            params = {}

        rst = self.tv.search_multi(queries=symbols, params=params)

        return rst

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def quotes(self,
               symbols: Union[str, List[str]],
               fields: List[str] = None) -> Union[Quote, Dict[str, Quote]]:
        return_single = isinstance(symbols, str)

        if fields is None:
            fields = [*Quote.model_fields.keys()]
        elif '*' in fields:
            fields = []

        fields = [Quote.fields_map().get(i, i) for i in fields or []]

        is_get_change_24h = len(set(fields) & set(['change_24h', 'change_24h_pct', 'low_24h', 'high_24h'])) > 0
        is_get_change_5d = len(set(fields) & set(['change_5d', 'change_5d_pct', 'low_5d', 'high_5d'])) > 0
        is_get_change_1m = len(set(fields) & set(['change_1m', 'change_1m_pct', 'low_1m', 'high_1m'])) > 0
        is_get_change_mtd = len(set(fields) & set(['change_mtd', 'change_mtd_pct', 'low_mtd', 'high_mtd'])) > 0
        is_get_change_ytd = len(set(fields) & set(['change_ytd', 'change_ytd_pct', 'low_ytd', 'high_ytd'])) > 0

        if True in [is_get_change_24h,
                    is_get_change_5d,
                    is_get_change_1m,
                    is_get_change_mtd,
                    is_get_change_ytd]:
            def _get_quotes_or_ohlcv(fn: str):
                if fn == 'current_quotes':
                    return self.tv.current_quotes(symbols, fields=fields)
                elif fn == 'ohlcv':
                    _ohlcv = self.ohlcv(symbols=symbols,
                                        freq='1D',
                                        total_candles=252 * 2,
                                        tzinfo='America/Chicago').reset_index()

                    _ohlcv['Date'] = _ohlcv['Date'].dt.tz_localize(None)

                    return _ohlcv

                return

            quotes, ohlcv = self.executor.map(_get_quotes_or_ohlcv, ['current_quotes', 'ohlcv'])
        else:
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

        if is_get_change_24h:
            perf_dict = self.calc_perf(ohlcv, '24H')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update={_k: _v for _k, _v in v.items() if _k in fields})

        if is_get_change_5d:
            perf_dict = self.calc_perf(ohlcv, '5D')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update={_k: _v for _k, _v in v.items() if _k in fields})

        if is_get_change_1m:
            perf_dict = self.calc_perf(ohlcv, '1M')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update={_k: _v for _k, _v in v.items() if _k in fields})

        if is_get_change_mtd:
            perf_dict = self.calc_perf(ohlcv, 'MTD')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update={_k: _v for _k, _v in v.items() if _k in fields})

        if is_get_change_ytd:
            perf_dict = self.calc_perf(ohlcv, 'YTD')

            for k, v in perf_dict.items():
                rst[k] = rst[k].model_copy(update={_k: _v for _k, _v in v.items() if _k in fields})

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

        ohlcv = self.tv.ohlcv(symbols=symbols,
                              freq=freq,
                              total_candles=total_candles,
                              charts=charts,
                              adjustment=adjustment.value)

        ohlcv = set_index_by_timestamp(ohlcv, tzinfo)
        ohlcv.index.rename(inplace=True, names={'timestamp': 'Date',
                                                'symbol': 'Symbol'})
        ohlcv.rename(axis=1, inplace=True, mapper={'open': 'Open',
                                                   'high': 'High',
                                                   'low': 'Low',
                                                   'close': 'Close',
                                                   'volume': 'Volume'})
        ohlcv.rename_axis(axis=1, inplace=True, mapper='Field')

        return ohlcv

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

    def correlations(self,
                     markets: Union[List[str]] = None,
                     exchanges: Union[List[str]] = None,
                     sort: Union[str, str] = None,
                     topn: int = None,
                     freq: int = '1D',
                     total_candles: int = 252,
                     tzinfo=None,
                     periods=['1D', '5D', '10D', '21D']) -> pd.DataFrame:
        if isinstance(markets, str):
            markets = [markets]

        if isinstance(exchanges, str):
            exchanges = [exchanges]

        sort_by, sort_order = sort

        payload = {
            'columns': ['name', sort_by],
            'range': [0, topn],
            'sort': {'sortBy': sort_by, 'sortOrder': sort_order},
            'markets': markets or [],
        }
        if exchanges:
            payload = deep_update(payload,
                                  {'filter': [{
                                      'left': 'exchange',
                                      'operation': 'in_range',
                                      'right': exchanges or []}]})

        # return payload
        assets = self.tv.scan(payload)
        symbols = pd.DataFrame(assets)['s']

        ohlcv = self.ohlcv(symbols=list(symbols),
                           freq=freq,
                           total_candles=total_candles,
                           tzinfo=tzinfo).stack().unstack('Symbol') \
            .rename_axis(['Date', 'Field'], axis=0).swaplevel().sort_index() \
            .ffill(axis=0).dropna(how='all')

        rst = _calc_corr(ohlcv, periods)

        return rst

    def calc_perf(self,
                  ohlcv: pd.DataFrame,
                  freq: str = '5d') -> Dict[str, Dict[str, Any]]:
        symbols = ohlcv.Symbol.unique()
        _ohlcv: pd.DataFrame = ohlcv.set_index(['Date', 'Symbol'])

        freq = freq.lower()
        freq_mapper = {
            '24h': '24H',
            '5d': 5,
            '1m': 21,
            'mtd': 'M',
            'ytd': 'Y',
        }
        freq_num: Union[int, str] = freq_mapper.get(freq, freq)

        perf_dict = {}
        for s in symbols:
            _ohlcv_sym: pd.DataFrame = _ohlcv.loc[:, s, :].copy()

            if isinstance(freq_num, str):
                _ohlcv_agg: pd.DataFrame = _ohlcv_sym.Close.groupby(_ohlcv_sym.index.to_period(freq_num)).last().rename('close').to_frame()
                _ohlcv_agg.loc[:, f'close_{freq}_prev'] = _ohlcv_agg.close.shift(1)
                _ohlcv_agg.loc[:, f'change_{freq}'] = _ohlcv_agg.close - _ohlcv_agg[f'close_{freq}_prev']
                _ohlcv_agg.loc[:, f'change_{freq}_pct'] = _ohlcv_agg[f'change_{freq}'] / _ohlcv_agg[f'close_{freq}_prev']
                _ohlcv_agg.loc[:, f'low_{freq}'] = _ohlcv_sym.Low.groupby(_ohlcv_sym.index.to_period(freq_num)).min()
                _ohlcv_agg.loc[:, f'high_{freq}'] = _ohlcv_sym.High.groupby(_ohlcv_sym.index.to_period(freq_num)).max()
                _ohlcv_sym = _ohlcv_agg

            elif isinstance(freq_num, int):
                _ohlcv_sym.rename({'Close': 'close'}, axis=1, inplace=True)
                _ohlcv_sym.loc[:, f'close_{freq}_prev'] = _ohlcv_sym.close.shift(freq_num)
                _ohlcv_sym.loc[:, f'change_{freq}'] = _ohlcv_sym.close - _ohlcv_sym[f'close_{freq}_prev']
                _ohlcv_sym.loc[:, f'change_{freq}_pct'] = _ohlcv_sym[f'change_{freq}'] / _ohlcv_sym[f'close_{freq}_prev']
                _ohlcv_sym.loc[:, f'low_{freq}'] = _ohlcv_sym.Low.rolling(freq_num).min()
                _ohlcv_sym.loc[:, f'high_{freq}'] = _ohlcv_sym.High.rolling(freq_num).max()

            cols_included = ['close',
                             f'change_{freq}',
                             f'change_{freq}_pct',
                             f'low_{freq}',
                             f'high_{freq}']

            perf_dict[s] = _ohlcv_sym[cols_included].iloc[-1].to_dict()

        return perf_dict


def _calc_corr(ohlcv: pd.DataFrame, periods: List[str]) -> pd.DataFrame:
    corr_ranks_ls: List[pd.DataFrame] = []

    for p in periods:
        closes = ohlcv.loc['Close']
        num_intervals = closes.resample(p).count().max().max()
        returns_fwd = closes.pct_change(-num_intervals)

        _corr: pd.DataFrame = returns_fwd.corr() \
            .rename_axis('s1', axis=0).rename_axis('s2', axis=1)

        top_corr = np.argsort(_corr)[:, -2]

        pairs = pd.DataFrame({'s1': _corr.index,
                              's2': _corr.columns[top_corr]})

        pairs_index = pd.MultiIndex.from_frame(pairs)

        _corr_ranks = _corr.stack().reindex(pairs_index).rename(p)

        corr_ranks_ls.append(_corr_ranks)

    corr_ranks = pd.concat(corr_ranks_ls, axis=1).rename_axis('period', axis=1) \
        .stack().rename('corr').reset_index().set_index(['period', 'corr']) \
        .sort_index().reset_index().set_index(['period', 's1', 's2'])

    return corr_ranks