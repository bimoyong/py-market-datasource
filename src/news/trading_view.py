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
              category: Union[BaseCategory, List[BaseCategory]] = None,
              from_date: datetime = None,
              to_date: datetime = None,
              items_per_page: int = 10) -> Paging:

        paging = self.list(category=category,
                           from_date=from_date,
                           to_date=to_date,
                           items_per_page=items_per_page)

        news_ls: List[News] = paging.data
        links = [i.source_id for i in news_ls]
        details = list(self.executor.map(self._detail, links))

        for i, news in enumerate(news_ls):
            if not isinstance(details[i], dict):
                continue

            news.description = details[i].get('shortDescription')

            html = self._json_to_html(details[i].get('astDescription'))
            news.html = self._parse_detail(html)
            news.text = self._parse_detail(html, return_html=False)

        return paging

    def list(self,
             category: Union[BaseCategory, List[BaseCategory]] = None,
             from_date: datetime = None,
             to_date: datetime = None,
             items_per_page: int = 10,
             page_number: int = 1) -> Paging:
        symbol = category

        url = join(self.BASE_URL, 'v2/headlines')

        params = {
            'client': 'web',
            'lang': 'en',
            'symbol': symbol,
        }

        headers = {
            **self.HEADERS,
        }

        resp = requests.request('GET', url, params=params, headers=headers,
                                timeout=self.TIMEOUT)

        data: Dict[str, Union[Dict[str, Any], Any]] = resp.json()

        if data.get('status') == 'error':
            raise ConnectionRefusedError(f'{__class__.__name__} refused request')

        rst = self._parse_list(data)

        return rst

    def detail(self,
               url: str,
               return_html: bool = True) -> str:
        url_path = url.removeprefix(f'{self.BASE_URL_WEB}/news/')

        data = self._detail(url_path[:url_path.find('-')])

        html = self._json_to_html(data.get('astDescription', {}))

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

        resp = requests.request('GET', url, headers=headers, params=params,
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

        metadata = data.get('meta', {}).get('page', {})
        size = metadata.get('size')
        total_pages = metadata.get('totalPages')
        total = metadata.get('total')

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

        if return_html:
            return soup.prettify()

        txt = soup.get_text(separator='\n')

        return txt

    def _json_to_html(self, json_data: Dict[str, Union[Dict[str, Any], Any]]):
        '''
        Function to convert JSON to HTML using custom mapping
        '''

        # Custom mapping from JSON types to HTML tags
        type_to_tag = {
            'root': 'div',           # Use a 'div' or a different container element
            'p': 'p',
            'table': 'table',
            'table-body': 'tbody',
            'table-row': 'tr',
            'table-data-cell': 'td',
            'text': None,            # Handle text nodes separately
        }

        def convert_node(node):
            if isinstance(node, str):
                return node

            # Get the tag based on the type
            # Default to 'div' if type is unknown
            tag = type_to_tag.get(node['type'], 'html')

            # Handle text nodes (no wrapping tag)
            if node['type'] == 'text':
                return node.get('text', '')

            # Start the HTML tag
            if tag:
                html = f'<{tag}>'
            else:
                html = ''

            # Process children nodes recursively
            if 'children' in node:
                for child in node['children']:
                    html += convert_node(child)

            # Close the HTML tag if necessary
            if tag:
                html += f'</{tag}>'

            return html

        return convert_node(json_data)
