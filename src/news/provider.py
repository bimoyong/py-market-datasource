from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Union

from models.news_enums import Category
from models.news_model import MasterData, Paging


class NewsProvider(ABC):
    def master_data(self) -> MasterData:
        rst = MasterData(categories=map(str.lower, Category._member_names_))

        return rst

    @abstractmethod
    def crawl(self,
              category: Union[Category, List[Category]] = None,
              from_date: datetime = None,
              to_date: datetime = None,
              items_per_page: int = 10) -> Paging:
        pass

    @abstractmethod
    def list(self,
             category: Union[Category, List[Category]] = None,
             from_date: datetime = None,
             to_date: datetime = None,
             items_per_page: int = 10,
             page_number: int = 1) -> Paging:
        pass

    @abstractmethod
    def detail(self, url: str, return_html: bool = True) -> str:
        pass
