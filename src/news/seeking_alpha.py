import re
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from datetime import datetime
from enum import Enum
from os.path import join
from typing import List, Union

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
    HEADERS = {
        'Cookie': 'LAST_VISITED_PAGE=%7B%22pathname%22%3A%22https%3A%2F%2Fseekingalpha.com%2Flatest-articles%22%2C%22pageKey%22%3A%22e5546f19-9f4a-4de0-a2f3-91b2603bf40e%22%7D; _px3=b3f50ef5942a4df485bb59f0d0f5d4662203733a8a6f6372c02234cad0847194:QZw578SmF4cI8m2ag0mYihDUObc8H6iWwhOgcr4ijUeHwsGixxdY9rUjkQo/aIyTDrRbszujsrpUznai5ykNFg==:1000:aL0Pvr0WY0hKc+34Zuu5+5t+B5rfYsrJgiLbtXK+dL++ZCoUL8Sit/K71GnaUPTeZuIXM/icwrP6ZlYlNuMhAKVBVXNQv32NGImoN8HElgRzXR618hlmp83KBmNZbBgTEZZUjZ57l4W0nC+djcxe2fYQPP8kBF+2AgYU9qWWqB1JpeFAn90CX1xXxEjWYBj631L4EixuqWsvPYboB4ePQjmbSt9IZ/eE47cIZK2Jv7Y=; _pxde=6eddb1908b3ed62853af3b89a3e42c8ed9f2bdae410a42c47169b8fc20219e73:eyJ0aW1lc3RhbXAiOjE3MTYwMjUyMjk3MzIsImZfa2IiOjB9; _ga_KGRFF2R2C5=GS1.1.1716025148.1.1.1716025212.60.0.0; __pat=-14400000; __tbc=%7Bkpex%7DLX-XgJEdaU1ESm2mfUFBwEHFbAh-xRoCe3F_n4DZ9FowA75AfFmA_eSFgY7p3f_X; xbc=%7Bkpex%7Ddst8s2i9a5DA4iTc25vlnA; __pvi=eyJpZCI6InYtMjAyNC0wNS0xOC0xNi0zOS0wOC00MDAtZmpwRGp0cXpodWtaZnNhMC1jMjhlMTVhOWI3OGZjZDZmNTFiZjkyNWRkODQ1OWNmMCIsImRvbWFpbiI6Ii5zZWVraW5nYWxwaGEuY29tIiwidGltZSI6MTcxNjAyNTIwNzc5MX0%3D; _pcid=%7B%22browserId%22%3A%22lwbx2ep34wun52fj%22%7D; _pctx=%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAE0RXQF8g; __hssc=234155329.3.1716025154905; __hssrc=1; __hstc=234155329.21e3dfd6d4e90238200cc746caf05ecc.1716025154905.1716025154905.1716025154905.1; _ga=GA1.1.950863998.1716025148; _gcl_au=1.1.1531433765.1716025148; _hjSessionUser_65666=eyJpZCI6IjU1NzJmNDdhLTcxMWUtNTAyOS1iNDRjLTQyOTAwNjY4NGIzMCIsImNyZWF0ZWQiOjE3MTYwMjUxNDgxMjcsImV4aXN0aW5nIjp0cnVlfQ==; hubspotutk=21e3dfd6d4e90238200cc746caf05ecc; _hjHasCachedUserAttributes=true; sailthru_content=3c5f57e561d9315a8a9a86be8720511eb6f09daf178879a54eed98528b6242aaad4605d955a87f844e9fc3137faeccc2; sailthru_pageviews=4; sailthru_visitor=9db42e01-7ffc-43fd-9425-3efdbd89e25f; _hjSession_65666=eyJpZCI6IjNjMzUzNTQwLTIxZDItNGNhNC05YjNlLTYyNTk5YjQ5NTdjMCIsImMiOjE3MTYwMjUxNDgxMjksInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; _sasource=; session_id=a5b3e993-a539-4faa-bcf5-3b0fd9b07040; _pxvid=79b56d70-14fa-11ef-a63f-90d0af1c3233; pxcts=79b57983-14fa-11ef-a63f-2002c463919f; machine_cookie=6615156694844',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': 'seekingalpha.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://seekingalpha.com/latest-articles',
        'Connection': 'keep-alive',
    }

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
        page_number = 1
        paging_sum = Paging()
        news_ls: List[News] = None

        while True:
            if news_ls is not None and len(news_ls) == 0:
                break

            if paging_sum.metadata is not None and page_number > paging_sum.metadata.total_pages:
                break

            try:
                time.sleep(self.THROTTLING_SECONDS)

                paging = self.list(symbol=symbol,
                                   category=category,
                                   from_date=from_date,
                                   to_date=to_date,
                                   items_per_page=items_per_page,
                                   page_number=page_number)
            except ConnectionRefusedError:
                page_number += 1
                continue

            news_ls = paging.data
            paging_sum.data.extend(news_ls)

            if not paging_sum.metadata:
                paging_sum.metadata = paging.metadata
            else:
                paging_sum.metadata.timestamp_min = min(paging.metadata.timestamp_min, paging_sum.metadata.timestamp_min)
                paging_sum.metadata.timestamp_max = max(paging.metadata.timestamp_max, paging_sum.metadata.timestamp_max)

            page_number += 1

        news_ls = paging_sum.data
        links = [i.link for i in news_ls]
        return_htmls = [True] * len(links)
        htmls = list(self.executor.map(self.detail, links, return_htmls))

        for i, news in enumerate(news_ls):
            if not isinstance(htmls[i], str):
                continue

            news.html = htmls[i]
            news.text = self._parse_detail(htmls[i], return_html=False)

        return paging_sum

    def list(self,
             symbol: str = None,
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
            html = str(soup_article)

            return html

        for img in (imgs := soup_article.find_all('img', {'src': re.compile('.png')})):
            img.replace_with(f"{img.get('src')}\n")

        for img in (imgs := soup_article.find_all('img', {'src': re.compile('.jpeg')})):
            img.replace_with(f"{img.get('src')}\n")

        txt = soup_article.get_text(separator='\n')

        return txt
