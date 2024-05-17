import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from datetime import datetime
from enum import Enum
from os.path import join
from typing import Any, Dict, List, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as date_parse

from models.news_enums import Category as BaseCategory
from models.news_model import News, Paging, PagingMetadata
from news.provider import NewsProvider


class Category(Enum):
    ALL = 'latest-articles'
    FINANCIAL = 'stock-ideas::financial'


class SeekingAlpha(NewsProvider):
    WORKERS_NO = 2
    BASE_URL = 'https://seekingalpha.com'

    HEADERS = {
        'Cookie': '_sasource=; session_id=53de4320-8728-4580-aaf8-590e0e953041; _px3=73d659c0ec71917e74f464d2311e1e5c8dfe07d8853ea87b4d3f181426af9ffb:D70Uf9d5AR9/1jhQKqmFFcCMSLp/zJn1e6JS0mUdbh9FWv3cadKUBseOdTLhlQXUbA3SzgiRKZNLu7Xzlq7oKw==:1000:W2a0SYgHi20twRbiFjmkL0mopFfjNlHdmngPqyTDvpfSo2FrdNlMGBMmvu+3HQtZulssVX1xiJaykgxH9Fl5Czdtyu/Kdc7wyj50ovop6X+AatjWM/XDZnyZzgI7r9Ud8NaABrpOLwUI3xe6L6hNkT96WA0nreH0Nhl1rL16MQhS3+4R9Op6VVmix3Wf14aa8ex4obEzowE9i4K+ThEQr3ZWVJYiUvmRF2Kd8gVrOHo=; _pxde=dff73e91cb5e1387d0f81e3efbd025fea174be5696141b48679853996ab1131a:eyJ0aW1lc3RhbXAiOjE3MTU5NDcwMjE4OTYsImZfa2IiOjB9; _ga_KGRFF2R2C5=GS1.1.1715940008.5.1.1715945640.60.0.0; LAST_VISITED_PAGE=%7B%22pageKey%22%3A%22e6e270f4-61f2-407d-bafe-95cf6b64509b%22%2C%22pathname%22%3A%22https%3A%2F%2Fseekingalpha.com%2Farticle%2F4693819-celestica-stock-close-to-its-fair-value-already-cls%22%7D; __hssrc=1; __hstc=234155329.acf9377fa701f69a3e964ce475d65297.1715911962881.1715935707709.1715940013718.3; hubspotutk=acf9377fa701f69a3e964ce475d65297; sailthru_content=e50456df42321a2ec24d743647c007ca2053f3eb9304470bdccfd2b70e22b5b3a6868281678e0269f2e30c72a59520f8e8d91b7f94d3c9bfa2c249220e11b6983722060a13864b436406e99876cebb82f0251524d6c5bdfecb6f06af6381eace7be0017fcefb858790642f69ca0d082dc68934db1a8a615dc31a02ddd20e0242c215c81107415182fdfc45f7f361e4659c8d493aee7ab8a1c2935241f51665512c5a37d7ed6dce43e64be461eba9ca62b052607f1273445f8b9e8fe729510c923d8a5289b7ac226022ecd03992b35b343c5f57e561d9315a8a9a86be8720511e864a387d4ab5a182517d0c04b543f065095ae167d7b5a8052ea6a2c74ef0b0d4; sailthru_visitor=98185970-a861-4c75-9d6c-d8c346775e68; __pat=-14400000; __tbc=%7Bkpex%7DHMtJG0yl0jTyuVXaBO6E9LBZF66-U-ZkJMs3aJz0yhIg3EzOKLpu3RnJgPgEuDMZ; _ga=GA1.1.310070056.1715911959; _gcl_au=1.1.203239099.1715911958; _hjSessionUser_65666=eyJpZCI6IjQ4MDliNzNmLTU4MWItNTY5MS05ZmQ2LTYzNGI3Y2FhMTk5ZiIsImNyZWF0ZWQiOjE3MTU5MTE5NTg1MTIsImV4aXN0aW5nIjp0cnVlfQ==; _pctx=%7Bu%7DN4IgrgzgpgThIC5QDYAMAWAjAJmQDgHZFQAHGKAMwEsAPREEAGhABcBPEqegNQA0QAvgOaRYAZRYBDFpHrkA5lQgtYUACZMQEKioCSGhADswAGxMCgA; xbc=%7Bkpex%7Dzea3C-i0C081qNk8E8uvYfnSp69gvqSXT6vBBf3xZqr7W5KNXQiQMi3AGsp3Vv05mE2Mw5HIjCl_TKK8o3gz1nkzjSn6ZjtLgMY6TdIdknhXKUKbiSYLqkgylZu7i_BwTPqjgagtCfVStiUhC13sDWiDMS0vkK7nyPv_isEvuAIN7CaTCiCXg7F5OOQ7qE9v; _hjHasCachedUserAttributes=true; _ig=60412687; __pvi=eyJpZCI6InYtMjAyNC0wNS0xNy0xNy0wMC0xMi0yNTYtQ0liOTJ0QjRvd21VNHEwYS1jZWU3YjNmNTJlMjY3MjAxM2ZlMmNjZTYxY2Y2ZWMxNCIsImRvbWFpbiI6Ii5zZWVraW5nYWxwaGEuY29tIiwidGltZSI6MTcxNTk0NDAxODYwOX0%3D; _pcid=%7B%22browserId%22%3A%22lwa1ocyhuh71vply%22%7D; machine_cookie=4461913391342; session_id=f4d5e7d2-b51b-4147-b9c0-ade72255f160; user_cookie_key=1ixejbh; user_id=60412687; user_nick=bimoyong; __tae=1715915683581; gk_user_access=1**1715915058; gk_user_access_sign=23fbf3f7cb5b863a69d20539b64df4909f7422f6; sapu=101; u_voc=; user_devices=; kppid=8klwdbbhp3z; user_remember_token=a1476196f7b953737ed3a4657e8c50f3cedc852d; sailthru_hid=f6e4a3b7d7149468bb6c13eabbc2696a6646c08b68914b3b8d0085a982ecb1eab1ee4f75d1fbee8d367bd9be; _sapi_session_id=QnBT1WTtx2g6O%2FXzKC37ts82Pp%2FHLt%2F6oc9491FY23y691P04dRdEH%2BFnZzRLIfjbyRwAIlEmDQHQGM77pCKno%2FfZ8FW8aY2cUIaYELluNdA0W84x%2BtCOzJ6xOZzBlgVKla6v2t80KDRXWwzDhEvhBzpHU20otZnYaNYhGB6hoonV%2BHqGAX0wxnpOtFZqkMMWwzMQO%2BRzqtGl5b0x0trsA4RQ4%2Fmd2Z7aAqcBUlLLF7iemaanliQAEBd1X%2FbMw%2FXfgJkfjXcvfwApxE2TyzTkUoqhwPPuB9qtvMXlh%2Fb1D5zUqM3RjpDO44EVsB3q6LgwRJYVX%2B4Thvwz4BSsWWVGDKDQ208vQhaRCm18B4BPg%2Frxk4JLviZVP2ibWllYMPq%2BGp4ma9GPfrwWJ15BSw8SsPy7VqgrxDcIXTh3q6alJ0tB4SLNKnbR7RbnKpfMsLkxcdMceS5sit8yUx5lhcAv9R6r5sW1U7hYsouQW6ruvOANE7lMhMzowSchYh7JRjiaYGVpguyZIvwqvFH2hr8KJNi9xXKmuWau735F8XmVr6WwRvje8r4qgxBsfFzYs1jgdXmeneMPZpMzHc3yh7B0m5vAnR%2Bnbyi380mGySsI8%2FYBxngDWZAGJadbvCBXBsvkMSSm%2BoekA0IXUFp--66Y5OBHmJ4pFDLna--5bfadZoSQB2UUtl8e1qpWQ%3D%3D; _igt=5007a76f-e92c-4410-dce0-97c89bf12b25; g_state={"i_p":1715919202965,"i_l":1}; _pxvid=efd91325-13f2-11ef-a066-a2281b5999f5; pxcts=efd92378-13f2-11ef-a066-77a8a7a45377',
        'Referer': 'https://seekingalpha.com/article/4693819-celestica-stock-close-to-its-fair-value-already-cls',
        'Cache-Control': 'max-age=0',
        'Host': 'seekingalpha.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

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
        page_number = 1
        paging_sum = Paging()
        news_ls: List[News] = None

        while news_ls is None or len(news_ls) > 0:
            paging = self.list(category=category,
                               from_date=from_date,
                               to_date=to_date,
                               items_per_page=items_per_page,
                               page_number=page_number)

            news_ls = paging.data
            paging_sum.data.extend(news_ls)

            if not paging_sum.metadata:
                paging_sum.metadata = paging.metadata

            page_number += 1

        news_ls = paging_sum.data
        links = [i.link for i in news_ls]
        return_htmls = [True] * len(links)
        htmls = list(self.executor.map(self.detail, links, return_htmls))

        for i, news in enumerate(news_ls):
            news.html = htmls[i]
            news.text = self._parse_detail(htmls[i], return_html=False)

        return paging_sum

    def list(self,
             category: Union[BaseCategory, List[BaseCategory]] = None,
             from_date: datetime = None,
             to_date: datetime = None,
             items_per_page: int = 10,
             page_number: int = 1) -> Paging:
        if category is None:
            category = Category.ALL
        else:
            category = Category[category.name]

        from_date = 0 if from_date is None else from_date.timestamp()
        to_date = 0 if to_date is None else to_date.timestamp()

        url = join(self.BASE_URL, 'api/v3/articles')

        params = {
            'filter[category]': category.value,
            'filter[since]': from_date,
            'filter[until]': to_date,
            'include': 'author,primaryTickers,secondaryTickers',
            'isMounting': True,
            'page[size]': items_per_page,
            'page[number]': page_number,
        }

        headers = {
            **self.HEADERS,
        }

        resp = requests.request('GET', url, params=params, headers=headers)

        data = resp.json()

        if 'blockScript' in data:
            raise ConnectionRefusedError('Seeking Alpha refused request')

        rst = self._parse_list(data)

        return rst

    def detail(self,
               url: str,
               return_html: bool = True) -> str:

        if self.BASE_URL not in url:
            url = join(self.BASE_URL, url.strip('/'))

        headers = {
            **self.HEADERS,
        }

        resp = requests.request('GET', url, headers=headers)

        html = resp.text

        if 'Access to this page has been denied.' in html:
            raise ConnectionRefusedError('Seeking Alpha refused request')

        rst = self._parse_detail(html=html, return_html=return_html)

        return rst

    def _parse_list(self, data: str) -> Paging:
        authors_dict = [{**i.get('attributes'), **i}
                        for i in data['included'] if i.get('type') == 'author']
        authors = pd.DataFrame(authors_dict)
        if not authors.empty:
            authors.set_index('id', inplace=True)

        news_ls = []
        for i in data.get('data'):
            if i.get('type') != 'article':
                continue

            attributes = i.get('attributes', {})
            relationships = i.get('relationships', {})

            source_id = i.get('id')

            timestamp: datetime = None
            timestamp_ts: int = None
            timestamp_iso: str = None
            with suppress(TypeError):
                timestamp_iso = attributes.get('publishOn')
                timestamp = date_parse(timestamp_iso)
                timestamp_ts = timestamp.timestamp()
                timestamp_iso = timestamp.isoformat()

            title = attributes.get('title')

            author: str = None
            with suppress(KeyError):
                author_id = relationships.get(
                    'author', {}).get('data', {}).get('id')
                author = authors.loc[author_id, 'nick']

            link: str = None
            with suppress(AttributeError):
                path = i.get('links', {}).get('self').strip('/')
                link = join(self.BASE_URL, path)

            news = News(source=__class__.__name__,
                        source_id=source_id,
                        timestamp=timestamp_iso,
                        timestamp_ts=timestamp_ts,
                        title=title,
                        author=author,
                        link=link)

            news_ls.append(news)

        metadata = data.get('meta', {}).get('page', {})
        size = metadata.get('size')
        total_pages = metadata.get('totalPages')
        total = metadata.get('total')

        timestamp_min: datetime = None
        timestamp_max: datetime = None
        with suppress(TypeError):
            timestamp_minmax = metadata.get('minmaxPublishOn', {})
            timestamp_min = datetime.fromtimestamp(timestamp_minmax.get('min'))
            timestamp_max = datetime.fromtimestamp(timestamp_minmax.get('max'))

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
            html = soup_article.prettify()

            return html

        for img in (imgs := soup_article.find_all('img', {'src': re.compile('.png')})):
            img.replace_with(f"{img.get('src')}\n")

        txt = soup_article.get_text()

        return txt
