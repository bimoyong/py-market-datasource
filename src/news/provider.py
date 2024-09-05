from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Union

import pandas as pd
from google.cloud.bigquery import Client as BigQueryClient

from infra.big_query import credentials, frame_to_big_query
from models.news_enums import Category
from models.news_model import MasterData, News, Paging


class NewsProvider(ABC):
    WORKERS_NO: int = None
    THROTTLING_SECONDS: int = None
    BASE_URL: str = None
    DB_TABLE: str = None

    def master_data(self) -> MasterData:
        rst = MasterData(categories=map(str.lower, Category._member_names_))

        return rst

    def crawl_to_db(self,
                    source: str = None,
                    symbol: str = None,
                    category: Union[Category, List[Category]] = None,
                    from_date: datetime = None,
                    to_date: datetime = None,
                    items_per_page: int = 10) -> None:
        qr_str_last_timestamp = '''
SELECT
  `timestamp`
FROM 
  `{table_name}`
WHERE
  `source` = "{source}"
ORDER BY
  `timestamp_ts` DESC
LIMIT
  1;
'''

        qr_str_last_timestamp = qr_str_last_timestamp.format(table_name=self.DB_TABLE,
                                                             source=source)

        if from_date is None:
            with BigQueryClient(credentials=credentials) as bq_client:
                qr = bq_client.query(qr_str_last_timestamp)
                _df: pd.DataFrame = qr.result().to_dataframe()
                if not _df.empty:
                    from_date = _df.iloc[-1].loc['timestamp']

        paging = self.crawl(symbol=symbol,
                            category=category,
                            from_date=from_date,
                            to_date=to_date,
                            items_per_page=items_per_page)
        news_ls: List[News] = paging.data

        df = pd.DataFrame.from_dict([news.model_dump() for news in news_ls])

        qr_str_exist = '''
SELECT
  `source_id`
FROM 
  `{table_name}`
WHERE
  `source` = "{source}"
  AND `source_id` IN ("{source_ids}");
'''

        qr_str_exist = qr_str_exist.format(table_name=self.DB_TABLE,
                                           source=source,
                                           source_ids='", "'.join(df['source_id'].astype(str)))

        with BigQueryClient(credentials=credentials) as bq_client:
            qr = bq_client.query(qr_str_exist)
            _df: pd.DataFrame = qr.result().to_dataframe()
            df = df.loc[~df['source_id'].isin(_df['source_id'])]

        if not df.empty:
            frame_to_big_query(df, self.DB_TABLE)

        return None

    @abstractmethod
    def crawl(self,
              symbol: str = None,
              category: Union[Category, List[Category]] = None,
              from_date: datetime = None,
              to_date: datetime = None,
              items_per_page: int = 10) -> Paging:
        pass

    @abstractmethod
    def list(self,
             symbol: str = None,
             category: Union[Category, List[Category]] = None,
             from_date: datetime = None,
             to_date: datetime = None,
             items_per_page: int = 10,
             page_number: int = 1) -> Paging:
        pass

    @abstractmethod
    def detail(self, url: str, return_html: bool = True) -> str:
        pass


class ProviderSelector():
    sources: Dict[str, NewsProvider] = {}
