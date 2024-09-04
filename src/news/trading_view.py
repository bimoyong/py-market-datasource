import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from os.path import join
from typing import Any, Dict, List, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup

from models.news_enums import Category as BaseCategory
from models.news_model import News, Paging, PagingMetadata
from news.provider import NewsProvider


class TradingView(NewsProvider):
    BASE_URL = 'https://news-headlines.tradingview.com'
    BASE_URL_WEB = 'https://www.tradingview.com'
    HEADERS = {}
    TIMEOUT = 30

    _executor: ThreadPoolExecutor = None

    @property
    def executor(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(self.WORKERS_NO)

        return self._executor

    def crawl(self,
              symbol: str = None,
              category: Union[BaseCategory, List[BaseCategory]] = None,
              from_date: datetime = None,
              to_date: datetime = None,
              items_per_page: int = 10) -> Paging:

        paging = self.list(symbol=symbol,
                           category=category,
                           from_date=from_date,
                           to_date=to_date,
                           items_per_page=items_per_page)

        news_ls: List[News] = paging.data
        ids = [i.source_id for i in news_ls]
        links = [i.link for i in news_ls]
        details = list(self.executor.map(self._detail, ids))
        htmls = list(self.executor.map(self.detail, links))

        for i, news in enumerate(news_ls):
            if not isinstance(details[i], dict):
                continue

            if not isinstance(htmls[i], str):
                continue

            news.description = details[i].get('shortDescription')
            news.html = htmls[i]
            news.text = self._parse_detail(htmls[i], return_html=False)

        return paging

    def list(self,
             symbol: str = None,
             category: Union[BaseCategory, List[BaseCategory]] = None,
             from_date: datetime = None,
             to_date: datetime = None,
             items_per_page: int = 10,
             page_number: int = 1) -> Paging:
        url = join(self.BASE_URL, 'v2/headlines')

        params = {
            'client': 'web',
            'lang': 'en',
            'symbol': symbol,
        }

        headers = {
            **self.HEADERS,
        }

        resp = requests.get(url, params=params, headers=headers,
                            timeout=self.TIMEOUT)

        data: Dict[str, Union[Dict[str, Any], Any]] = resp.json()

        if data.get('status') == 'error':
            raise ConnectionRefusedError(f'{__class__.__name__} refused request')

        rst = self._parse_list(data)

        return rst

    def detail(self,
               url: str,
               return_html: bool = True) -> str:
        resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)

        html = resp.text

        rst = self._parse_detail(html=html, return_html=return_html)

        return rst

    def _detail(self, source_id: str) -> Dict[str, Union[Dict[str, Any], Any]]:
        url = join(self.BASE_URL, 'v2/story')

        headers = {
            **self.HEADERS,
        }

        params = {
            'id': source_id,
            'lang': 'en',
        }

        resp = requests.get(url, params=params, headers=headers,
                            timeout=self.TIMEOUT)

        data: Dict[str, Union[Dict[str, Any], Any]] = resp.json()

        if data.get('status') == 'error':
            raise ConnectionRefusedError(f'{__class__.__name__} refused request')

        return data

    def _parse_list(self, data: Dict[str, Union[Dict[str, Any], Any]]) -> Paging:
        news_ls = []

        for i in data.get('items', []):
            news = News(source=self.__class__.__name__,
                        source_id=i.get('id'),
                        timestamp=pd.to_datetime(i.get('published'), unit='s').isoformat(),
                        timestamp_ts=i.get('published'),
                        title=i.get('title'),
                        author=i.get('provider'),
                        link=f"{self.BASE_URL_WEB}{i.get('storyPath')}")

            news_ls.append(news)

        size = len(news_ls)
        total_pages = 1
        total = len(news_ls)

        timestamp_min: datetime = None
        timestamp_max: datetime = None

        paging_metadata = PagingMetadata(size=size,
                                         total_pages=total_pages,
                                         total=total,
                                         timestamp_min=timestamp_min,
                                         timestamp_max=timestamp_max)

        page = Paging(data=news_ls,
                      metadata=paging_metadata)

        return page

    def _parse_detail(self,
                      html: str,
                      return_html: bool = True) -> str:
        soup = BeautifulSoup(html, 'html.parser')

        soup_article = soup.find('article')
        if not soup_article:
            return None

        if return_html:
            html = str(soup_article)

            return html

        for img in (imgs := soup_article.find_all('img', {'src': re.compile('.png')})):
            img.replace_with(f"{img.get('src')}\n")

        for img in (imgs := soup_article.find_all('img', {'src': re.compile('.jpeg')})):
            img.replace_with(f"{img.get('src')}\n")

        txt = soup_article.get_text(separator='\n')

        return txt
