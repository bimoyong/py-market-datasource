from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Union

import pandas as pd
from cachetools import TTLCache
from google.cloud.bigquery import Client as BigQueryClient


class TickDataProvider(ABC):
    WORKERS_NO: int = None

    BASE_URL: str = None
    USERNAME: str = None
    PASSWORD: str = None
    TOKEN_TTL: int = None

    _executor: ThreadPoolExecutor = None
    _token_cache: TTLCache = None

    @property
    def executor(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(self.WORKERS_NO)

        return self._executor

    @property
    def token_cache(self) -> TTLCache:
        if not self._token_cache:
            self._token_cache = TTLCache(maxsize=1, ttl=self.TOKEN_TTL)

        return self._token_cache

    @property
    def access_token(self) -> str:
        if not self.token_cache:
            tokens = self.fetch_token()
            self.token_cache['token'] = tokens

        return self.token_cache['token'].get('access_token')

    @property
    def refresh_token(self) -> str:
        if not self.token_cache:
            tokens = self.fetch_token()
            self.token_cache['token'] = tokens

        return self.token_cache['token'].get('refresh_token')

    @abstractmethod
    def fetch_token(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_files(self,
                   from_date: datetime = None,
                   to_date: datetime = None) -> pd.DataFrame:
        pass

    def download_files_background(self,
                                  workers_no: int = 4) -> None:
        pass

    @abstractmethod
    def download_file(self,
                      filename: Union[str, List[str]],
                      force=False) -> None:
        pass
