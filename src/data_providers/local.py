from os.path import exists, join
from typing import List, Union

import pandas as pd
import pytz

from data_providers.enums import Adjustment
from data_providers.tradingview_provider import TradingViewProvider


class Local(TradingViewProvider):
    @property
    def filename(self):
        return join('/tmp', f'{hex(id(self))}.h5')

    def ohclv(self,
              symbols: Union[str, List[str]],
              freq: str,
              total_candles: int,
              charts: List[str] = None,
              adjustment=Adjustment.DIVIDENDS,
              tzinfo: pytz.BaseTzInfo = pytz.UTC) -> pd.DataFrame:

        df: pd.DataFrame

        if exists(self.filename):
            with pd.HDFStore(self.filename) as store:
                df = store.get('ohclv')
                if 'symbol' and 'timestamp' in df:
                    df = df.set_index(['symbol', 'timestamp'])
        else:
            df = super().ohclv(symbols,
                               freq,
                               total_candles,
                               charts,
                               adjustment,
                               tzinfo)

            with pd.HDFStore(self.filename) as store:
                store.put('ohclv', df.reset_index())

        return df
