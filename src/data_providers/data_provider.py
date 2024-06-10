from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

import pandas as pd
import pytz

from data_providers.enums import Adjustment
from models.data_models import Quote


class DataProvider(ABC):
    WORKERS_NO: int = None

    @abstractmethod
    def search(self,
               symbols: List[str],
               params: Dict[str, Any] = None) -> Dict[str, Union[None, Dict[str, Any]]]:
        pass

    @abstractmethod
    def quotes(self,
               symbols: Union[str, List[str]],
               fields: List[str] = None) -> Union[Quote, Dict[str, Quote]]:
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
