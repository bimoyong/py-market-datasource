from os.path import exists, join
from typing import List, Union

import pandas as pd
import pytz

from data_providers.enums import Adjustment
from data_providers.tradingview import TradingView


class Local(TradingView):
    @property
    def filename(self):
        return join('/tmp', f'{hex(id(self))}.h5')

    def ohlcv(self,
              symbols: Union[str, List[str]],
              interval: str,
              total_candle: int,
              charts: List[str] = None,
              adjustment=Adjustment.DIVIDENDS,
              tzinfo: pytz.BaseTzInfo = pytz.UTC) -> pd.DataFrame:

        df: pd.DataFrame

        if exists(self.filename):
            with pd.HDFStore(self.filename) as store:
                df = store.get('ohlcv')
                if 'symbol' and 'timestamp' in df:
                    df = df.set_index(['symbol', 'timestamp'])
        else:
            df = super().ohlcv(symbols, interval, total_candle, charts, adjustment, tzinfo)

            with pd.HDFStore(self.filename) as store:
                store.put('ohlcv', df.reset_index())

        return df
