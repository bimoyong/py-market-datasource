from abc import ABC, abstractmethod
from typing import Dict, List, Union

import pandas as pd
import pytz

from data_providers.enums import Adjustment
from data_providers.models import Quote


class DataProvider(ABC):
    @abstractmethod
    def quote(self, symbols: Union[str, List[str]]) -> Union[Quote, Dict[str, Quote]]:
        pass

    @abstractmethod
    def ohlcv(self,
              symbols: Union[str, List[str]],
              interval: str,
              total_candle: int,
              charts: List[str] = None,
              adjustment=Adjustment.DIVIDENDS,
              tzinfo: pytz.BaseTzInfo = pytz.UTC) -> pd.DataFrame:
        pass
