# @title Define TradingView class

import json
import random
import re
import string
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from itertools import repeat
from time import perf_counter
from typing import Any, Dict, List, Union

import pandas as pd
from pydantic.v1.utils import deep_update
from requests import get, post
from websocket import WebSocket, create_connection

_SCANNER_URL_ = 'https://scanner.tradingview.com'
_API_URL_ = 'https://symbol-search.tradingview.com/symbol_search/v3'
_ECONOMIC_URL = 'https://economic-calendar.tradingview.com'
_WS_URL_ = 'wss://prodata.tradingview.com/socket.io/websocket?&type=chart'

_CHARTS_SETTINGS = {
    'ema10': ['Script@tv-scripting-101!', {'text': 'bmI9Ks46_u96awLDSJj8c4xVHubmEMw==_E3G6GqoJr5rLISOgO9nBsoc2e4nLvKBi1q5InR7AttexejdPJoAOC8z/vvUAqlCMpPiv11uwGy2v0EG7phDcDFZiaEKMt/1ooB+5hPaSKK7EuUzKTIGLFzbLtwjwO5Z7jR11jP1Z2MsAt9cN0smrwQMTjphpEDRVvzDqBcB2wZRR7BxQeQ9j7ynKMseInC5G34ToyLmrle0+4Dcw9IhWNkvpGLKhODeEIdjlfm6ZzEAu3cuuLIx9Kn1f1h6AdSVccLpVDzTy67dQ9TanhaaIy5Ogz+kuRYKTkkP63IaXvEn03t29DDUoWMxzQolZuBW6vDVAbHMgPm52yHN88uvJ5px4IGDbuRdJlTLrMpbgG4SAP+DWhKL6wbsu9MfYfe4bGMzfvF7vE/ltqlycHIHIjOS2SfFrqxmVg4eH1+V+/7g0JbnCvSJAeY/RKUCx+jJZa+Gm0mvhmvz+abYWJLpqTpBctZ8kYI+6EGVXgshUZrkahn+S0oGnvwOB4NzLMCSX9NLidpDZKuDuI2Whfb08toOkoGiF8JYhvnotLZSDa0DTDhwZtqQf0hAChG/3RK42S75LxcZwyTl39emlxdU9uDoDV+d/NHZFao+FSoNhSkTsqOnfuVp5l3V1yop8Psh64sbs2A1cGqu1', 'pineId': 'STD;EMA', 'pineVersion': '29.0', 'pineFeatures': {'v': '{\'indicator\':1,\'plot\':1,\'ta\':1}', 'f': True, 't': 'text'}, 'in_0': {'v': 10, 'f': True, 't': 'integer'}, 'in_1': {'v': 'close', 'f': True, 't': 'source'}, 'in_2': {'v': 0, 'f': True, 't': 'integer'}, 'in_3': {'v': 'EMA', 'f': True, 't': 'text'}, 'in_4': {'v': 5, 'f': True, 't': 'integer'}, 'in_5': {'v': '', 'f': True, 't': 'resolution'}, 'in_6': {'v': True, 'f': True, 't': 'bool'}}],
    'ema21': ['Script@tv-scripting-101!', {'text': 'bmI9Ks46_iAX8exg0i/mBcDvY1smolQ==_jO5cug1NHY+z8s0TpdR7Fev6EEMhjfmTU5mbl5iuXE4UOVqejOvpDjiTL5t3fgGOAjkPxvD/uGIuqepaXnEzXZf3Dfcivitq36RSeVQJZkcjMjW9VjSBs2JBC46Z2XEHj1oKNZSZOQlx1NXqJiPhl4wEzpiWIDdgSG2mxoZXjp+4Bq9+C9cMfH0E9t8pFWkvKeckFaN5P8ZtdAR8k/UBSaMd0r68pvEpiLdujfRKb2xjbIQMsnJzqq0/BRMx0rFzK1OHtZLyqaxdHDjIsmwVmyd2OwzJg498v08fSIrlK5VNnlrxk/RUc+ZVrWVY/eH4XmqMuzaNha3HtFUO3wjQip8ISjaWgv+WwGPAnMgVVWSSJrZ9Urtj6+NIbwCRctEaMLKzHI01uk8+JXlzs5pqjzmAyaXvgMkKVvhp5+NjRxKHyHfCD9Gd+UNN8QoAPnRVied3ETVygHjvK6eoD9Wb5TvS9U4sWoShZ8QBX28FinVjbNDYxq/RUTrcevujlasFaD7Y4gbGqakbVBjJx+xNVzbzA4usJMEeCOd9ahtX2HtJdajXxFZkZPImRk+kMtuNSElCq2E10PSn6jFEcHYnOkwF43wDilGsMHWJDI9gXr4nCUqfWBBn8XPrOJVdWyZ7GIxOl9ZOn1ix', 'pineId': 'STD;EMA', 'pineVersion': '29.0', 'pineFeatures': {'v': '{\'indicator\':1,\'plot\':1,\'ta\':1}', 'f': True, 't': 'text'}, 'in_0': {'v': 21, 'f': True, 't': 'integer'}, 'in_1': {'v': 'close', 'f': True, 't': 'source'}, 'in_2': {'v': 0, 'f': True, 't': 'integer'}, 'in_3': {'v': 'EMA', 'f': True, 't': 'text'}, 'in_4': {'v': 5, 'f': True, 't': 'integer'}, 'in_5': {'v': '', 'f': True, 't': 'resolution'}, 'in_6': {'v': True, 'f': True, 't': 'bool'}}],
    'ema50': ['Script@tv-scripting-101!', {'text': 'bmI9Ks46_YgiQhsSwDdbNYHsEzTaxnA==_tysyiC9xdsEwtdmdMBSVgXuVvcZQ9j6XhIppaillwsxzP5xbNHizoC2fq0d6Q6EZeh3JWFos4nGmxiOETJ4ncnF0L/i6laHxlvePKlj2JEbxW5NGFl5l2KgufioukfuvBYZK/wIWE/3hLrlxXITNc1MWs10LKta7PyhbyJ2gW6G8S+VU0P4L4JBVQurjsKg7vFM9IiSGgZ1MYb655UzYrm9q4VuIlFVj3wQsYj+xf2lK947wZETX1p8T3moRqYmpZ32GT6V5Krk2pVttLcUIAu1pzUOC6cw1f7PNI7dmOskToyk4TpxiVnqbZRRmj2N+vPdb/nXCSQOLH3fX3McEz6uguxb0MBQgnbCMrdV6bDtVB5xiCfYjA0uoxqCH7kKdzhQbRWVO8J6M+NZkxvPI7A4EJtgYFiRKEOjYO74BeW0UIj904Ms9NAYN6MnU28GjQ895q7AmIkyP/RO9z2yNU5Obnt4VZhJoLsWU+sfMFK0VdoPAoPK52EjeUq7gW3Bfd9ig2/V5dlcNPn55R5HY8Hs5lq6iTpH2rM2wr2s7q4VEfbLQZw7mHNm01btpH7MSuuxgHBJc7DcN9uxRYViDQw666TMjWXflJFzB3WA/NotrRbAH9KWTMISrtc9XunRjd+plBbUOyNPR', 'pineId': 'STD;EMA', 'pineVersion': '29.0', 'pineFeatures': {'v': '{\'indicator\':1,\'plot\':1,\'ta\':1}', 'f': True, 't': 'text'}, 'in_0': {'v': 50, 'f': True, 't': 'integer'}, 'in_1': {'v': 'close', 'f': True, 't': 'source'}, 'in_2': {'v': 0, 'f': True, 't': 'integer'}, 'in_3': {'v': 'EMA', 'f': True, 't': 'text'}, 'in_4': {'v': 5, 'f': True, 't': 'integer'}, 'in_5': {'v': '', 'f': True, 't': 'resolution'}, 'in_6': {'v': True, 'f': True, 't': 'bool'}}],
    'ema100': ['Script@tv-scripting-101!', {'text': 'bmI9Ks46_YgiQhsSwDdbNYHsEzTaxnA==_tysyiC9xdsEwtdmdMBSVgXuVvcZQ9j6XhIppaillwsxzP5xbNHizoC2fq0d6Q6EZeh3JWFos4nGmxiOETJ4ncnF0L/i6laHxlvePKlj2JEbxW5NGFl5l2KgufioukfuvBYZK/wIWE/3hLrlxXITNc1MWs10LKta7PyhbyJ2gW6G8S+VU0P4L4JBVQurjsKg7vFM9IiSGgZ1MYb655UzYrm9q4VuIlFVj3wQsYj+xf2lK947wZETX1p8T3moRqYmpZ32GT6V5Krk2pVttLcUIAu1pzUOC6cw1f7PNI7dmOskToyk4TpxiVnqbZRRmj2N+vPdb/nXCSQOLH3fX3McEz6uguxb0MBQgnbCMrdV6bDtVB5xiCfYjA0uoxqCH7kKdzhQbRWVO8J6M+NZkxvPI7A4EJtgYFiRKEOjYO74BeW0UIj904Ms9NAYN6MnU28GjQ895q7AmIkyP/RO9z2yNU5Obnt4VZhJoLsWU+sfMFK0VdoPAoPK52EjeUq7gW3Bfd9ig2/V5dlcNPn55R5HY8Hs5lq6iTpH2rM2wr2s7q4VEfbLQZw7mHNm01btpH7MSuuxgHBJc7DcN9uxRYViDQw666TMjWXflJFzB3WA/NotrRbAH9KWTMISrtc9XunRjd+plBbUOyNPR', 'pineId': 'STD;EMA', 'pineVersion': '29.0', 'pineFeatures': {'v': '{\'indicator\':1,\'plot\':1,\'ta\':1}', 'f': True, 't': 'text'}, 'in_0': {'v': 100, 'f': True, 't': 'integer'}, 'in_1': {'v': 'close', 'f': True, 't': 'source'}, 'in_2': {'v': 0, 'f': True, 't': 'integer'}, 'in_3': {'v': 'EMA', 'f': True, 't': 'text'}, 'in_4': {'v': 5, 'f': True, 't': 'integer'}, 'in_5': {'v': '', 'f': True, 't': 'resolution'}, 'in_6': {'v': True, 'f': True, 't': 'bool'}}],
    'ema200': ['Script@tv-scripting-101!', {'text': 'bmI9Ks46_YgiQhsSwDdbNYHsEzTaxnA==_tysyiC9xdsEwtdmdMBSVgXuVvcZQ9j6XhIppaillwsxzP5xbNHizoC2fq0d6Q6EZeh3JWFos4nGmxiOETJ4ncnF0L/i6laHxlvePKlj2JEbxW5NGFl5l2KgufioukfuvBYZK/wIWE/3hLrlxXITNc1MWs10LKta7PyhbyJ2gW6G8S+VU0P4L4JBVQurjsKg7vFM9IiSGgZ1MYb655UzYrm9q4VuIlFVj3wQsYj+xf2lK947wZETX1p8T3moRqYmpZ32GT6V5Krk2pVttLcUIAu1pzUOC6cw1f7PNI7dmOskToyk4TpxiVnqbZRRmj2N+vPdb/nXCSQOLH3fX3McEz6uguxb0MBQgnbCMrdV6bDtVB5xiCfYjA0uoxqCH7kKdzhQbRWVO8J6M+NZkxvPI7A4EJtgYFiRKEOjYO74BeW0UIj904Ms9NAYN6MnU28GjQ895q7AmIkyP/RO9z2yNU5Obnt4VZhJoLsWU+sfMFK0VdoPAoPK52EjeUq7gW3Bfd9ig2/V5dlcNPn55R5HY8Hs5lq6iTpH2rM2wr2s7q4VEfbLQZw7mHNm01btpH7MSuuxgHBJc7DcN9uxRYViDQw666TMjWXflJFzB3WA/NotrRbAH9KWTMISrtc9XunRjd+plBbUOyNPR', 'pineId': 'STD;EMA', 'pineVersion': '29.0', 'pineFeatures': {'v': '{\'indicator\':1,\'plot\':1,\'ta\':1}', 'f': True, 't': 'text'}, 'in_0': {'v': 200, 'f': True, 't': 'integer'}, 'in_1': {'v': 'close', 'f': True, 't': 'source'}, 'in_2': {'v': 0, 'f': True, 't': 'integer'}, 'in_3': {'v': 'EMA', 'f': True, 't': 'text'}, 'in_4': {'v': 5, 'f': True, 't': 'integer'}, 'in_5': {'v': '', 'f': True, 't': 'resolution'}, 'in_6': {'v': True, 'f': True, 't': 'bool'}}],
    'bbands20': ['Script@tv-scripting-101!', {'text': 'bmI9Ks46_oD+tpF2k+3I4ptfWVB5zAg==_SzZQ0i7zeu6zfw05iX1nk5+LTl+Ozp0UXh/XSlybKgscP8ebiBDx4Bfzfvudeaf7wjFo37+jrCTv08wHOexvDkKu+j2V37Wc13uTglDYIkVkKMdhzpG0h8uUnnRkksgkJNScvfM/FUxTdaQAYuQ+4CrejfduQndMYc+Uvf+0MzX7lHGMHmprn4YuSi4cSrKoyOD0lJkMMT85eaCXHWooNyUNzfBqXufrBwx5CZZdJgY8FvNn+zB4meN3snRLjkehFp7K+R1g53fN5x5LinZCqFAw91QEGa2/+p/nYQ61rdyMVgnJjRox4esZFaHaoqxFB45J5EtomRXrtENkHnMrppomgrTRKQkvA0nzD7ft1+gkac5zWR6dxxgyxWieJ/Kgol18+kOEr4ZfA1Cia8OrQ5aPJ3MHxrIjl8f//eNc60tvNKQcfqT8KbgU23hUOBSaYGBYz/rlaJKlMmGPVtMqsyFpYKKVNm+jG+prrU5Nj3+r8NOY9o6vtqlC4m1MeF2bafyr/tnhz04MK5zbQtzJxzuOoxftOQUker7CLlTTDrBU9VqC9tAmFhiC71sLD1tCPllTaZ2t4GqYEGf4xHiImRK2q1dv9QijF4JkP19q1/8EoR0lRF/Sfdm6PMPrPTY8QTeCq0DL649avSHXQg4JWsPwX/66wGbiAoiaXJ+uhsuj7Y8W15XWS2nK+k4Ya8ZwM1Qm+MIfrQH00kwi', 'pineId': 'STD;Bollinger_Bands', 'pineVersion': '29.0', 'pineFeatures': {'v': '{"indicator":1,"plot":1,"ta":1}', 'f': True, 't': 'text'}, 'in_0': {'v': 20, 'f': True, 't': 'integer'}, 'in_1': {'v': 'SMA', 'f': True, 't': 'text'}, 'in_2': {'v': 'close', 'f': True, 't': 'source'}, 'in_3': {'v': 2, 'f': True, 't': 'float'}, 'in_4': {'v': 0, 'f': True, 't': 'integer'}, 'in_5': {'v': '', 'f': True, 't': 'resolution'}, 'in_6': {'v': True, 'f': True, 't': 'bool'}}],
}


class TradingViewClient:
    def __init__(self,
                 username='',
                 password='',
                 token='',
                 market='',
                 workers_no=1) -> None:
        self._username = username
        self._password = password
        self._market = market
        self._token = token
        self._executor = ThreadPoolExecutor(max_workers=workers_no or 1)

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def market(self) -> str:
        return self._market

    @property
    def token(self) -> str:
        if not self._token:
            self._token = _get_auth_token(self.username, self.password)
        return self._token

    @property
    def executor(self) -> ThreadPoolExecutor:
        return self._executor

    def current_quotes(self,
                       symbols: Union[str, List[str]],
                       fields: List[str] = None) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        return_single = isinstance(symbols, str)
        _symbols = [symbols] if return_single else symbols

        # create tunnel
        headers = json.dumps({'Origin': 'https://data.tradingview.com'})
        ws = create_connection(_WS_URL_, headers=headers)
        sess = _generate_session('cs_')

        # Send messages
        if self.token:
            _send_message(ws, 'set_auth_token', [self.token])
        else:
            _send_message(ws, 'set_auth_token', ['unauthorized_user_token'])

        # Then send a message through the tunnel
        _send_message(ws, 'set_data_quality', ['high'])
        _send_message(ws, 'quote_create_session', [sess])

        if fields is not None:
            _send_message(ws, 'quote_set_fields', [sess, *fields])

        for i in _symbols:
            _send_message(ws, 'quote_add_symbols', [sess, i])

        # Start job
        rst = _socket_quote(ws,
                            symbols=symbols)

        quotes = rst[sess]

        if return_single:
            k = next(iter(quotes.keys()))
            return quotes[k]

        return quotes

    def realtime_quotes(self,
                        symbols: Union[str, List[str]],
                        callback: callable) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        return_single = isinstance(symbols, str)
        _symbols = [symbols] if return_single else symbols
        fields = ['lp', 'ch', 'lp_time', 'chp', 'volume']

        # create tunnel
        headers = json.dumps({'Origin': 'https://data.tradingview.com'})
        ws = create_connection(_WS_URL_, headers=headers)
        sess = _generate_session('qs_')

        # Send messages
        if self.token:
            _send_message(ws, 'set_auth_token', [self.token])
        else:
            _send_message(ws, 'set_auth_token', ['unauthorized_user_token'])

        _send_message(ws, 'set_data_quality', ['high'])
        _send_message(ws, 'quote_create_session', [sess])

        if fields is not None:
            _send_message(ws, 'quote_set_fields', [sess, *fields])

        for i in _symbols:
            _send_message(ws, 'quote_add_symbols', [sess, i])

        # Start job
        _ = _socket_quote(ws,
                          symbols=symbols,
                          realtime=True,
                          callback=callback)

    def ohlcv(self,
              symbols: Union[str, List[str]],
              freq: str,
              total_candles: int,
              charts: List[str] = None,
              adjustment='dividends') -> pd.DataFrame:
        symbols = [symbols] if isinstance(symbols, str) else symbols
        total_candles += 1  # preserve 1 bar because TradingView returns less than 1 bar
        charts = charts or []

        # create tunnel
        headers = json.dumps({'Origin': 'https://data.tradingview.com'})
        ws = create_connection(_WS_URL_, headers=headers)

        # Send messages
        if self.token:
            _send_message(ws, 'set_auth_token', [self.token])
        else:
            _send_message(ws, 'set_auth_token', ['unauthorized_user_token'])

        sess_ls = [_generate_session('cs_') for _ in symbols]
        sess_symbol_mapper = dict(zip(sess_ls, symbols))
        sessions_completed: Dict[str, bool] = {}

        # Then send a message through the tunnel
        _send_message(ws, 'set_data_quality', ['high'])
        for _sess, _symbol in sess_symbol_mapper.items():
            _send_message(ws, 'chart_create_session', [_sess, ''])
            _send_message(ws, 'resolve_symbol', [_sess, 'sds_sym', "={\"adjustment\":\"" + adjustment + "\",\"currency-id\":\"USD\",\"symbol\":\"" + _symbol + "\"}"])
            _send_message(ws, 'create_series', [_sess, 's_ohlcv', 's', 'sds_sym', str(freq), total_candles, ""])
            sessions_completed = deep_update(sessions_completed, {f'{_sess}__s_ohlcv': False})

            for chart in charts:
                chart_setting = _CHARTS_SETTINGS[chart]
                _send_message(ws, 'create_study', [_sess, f's_{chart}', 'st1', 's_ohlcv', *chart_setting])
                sessions_completed = deep_update(sessions_completed, {f'{_sess}__s_{chart}': False})

        # Start job
        df = _parse_bar_charts(ws, sessions_completed=sessions_completed)

        df['symbol'] = df.apply(lambda x: sess_symbol_mapper[x['session']], axis=1)
        df = df.drop('session', axis=1).reset_index().set_index(['timestamp', 'symbol'])
        df = df.loc[~df.index.duplicated(keep='first')]

        return df

    def search_multi(self,
                     queries: List[str],
                     params: Dict[str, Any]) -> Dict[str, Union[None, Dict[str, Any]]]:
        search_iter = self._executor.map(self.search,
                                         queries,
                                         repeat(params.get('country', 'US')),
                                         repeat(params.get('exchange', '')),
                                         repeat(params.get('search_type', '')),
                                         repeat(params.get('economic_category', '')),
                                         repeat(params.get('start', 0)))

        resp = dict(zip(queries, search_iter))

        return resp

    def search(self,
               query: str,
               country: str = 'US',
               exchange: str = '',
               search_type: str = '',
               economic_category: str = '',
               start: int = 0) -> Union[None,
                                        Dict[str, Any],
                                        Dict[str, Union[int, List[Dict[str, Any]]]]]:
        # text = what you want to search!
        # search_type = 'stocks' | 'funds' | 'futures' | 'forex' | 'crypto' | 'index' | 'bond' | 'economic' | 'options'
        # country = 'US'
        # it returns first matching item
        params = {
            'text': query,
            'country': country.upper(),
            'exchange': exchange,
            'search_type': search_type,
            'economic_category': economic_category,
            'start': start,
        }
        headers = headers = {
            'Accept': 'application/json',
            'Origin': 'https://www.tradingview.com',
        }

        res = get(_API_URL_, params=params, headers=headers, timeout=60)
        if res.status_code != 200:
            raise ConnectionError(f'Client returns error "{res.status_code} {res.content}"')

        res = res.json()

        if not res.get('symbols'):
            return None

        if res['symbols'][0].get('symbol') == query:
            return res['symbols'][0]

        return res

    def economic_calendar(self,
                          from_date: str = None,
                          to_date: str = None,
                          countries: List[str] = None,
                          fetch_related_events=False) -> List[Dict[str, Any]]:
        url = f'{_ECONOMIC_URL}/events'

        headers = {
            'origin': 'https://www.tradingview.com'
        }

        params = {
            'from': from_date,
            'to': to_date,
        }

        if isinstance(countries, list):
            params['countries'] = ','.join(countries)

        resp = get(url, params=params, headers=headers, timeout=60)

        if resp.status_code != 200:
            raise ConnectionError(f'Client returns error "{resp.status_code} {resp.content}"')

        data = resp.json()
        status = data.get('status')

        if status != 'ok':
            raise ConnectionError(f'Client returns error "{status} {data.get("errmsg")}"')

        result = data.get('result')

        if fetch_related_events:
            event_ids = [i.get('id') for i in result]
            events_ls = list(self._executor.map(self.economic_calendar_related_events, event_ids))

            for i, _ in enumerate(result):
                result[i]['events'] = events_ls[i]

        return result

    def economic_calendar_related_events(self, event_id: str) -> List[Dict[str, Any]]:
        url = f'{_ECONOMIC_URL}/related_events'

        headers = {
            'origin': 'https://www.tradingview.com'
        }

        params = {
            'eventId': event_id,
            'countback': 8,
        }

        resp = get(url, params=params, headers=headers, timeout=60)

        if resp.status_code != 200:
            raise ConnectionError(f'Client returns error "{resp.status_code} {resp.content}"')

        data = resp.json()
        status = data.get('status')

        if status != 'ok':
            return []

        result = data.get('result')

        return result

    def scan(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = f'{_SCANNER_URL_}/global/scan'

        headers = {
            'Content-Type': 'application/json'
        }

        resp = post(url, data=json.dumps(payload), headers=headers, timeout=60)

        if resp.status_code != 200:
            raise ConnectionError(f'Client returns error "{resp.status_code} {resp.content}"')

        data = resp.json()

        error = data.get('error')
        if error:
            raise ConnectionError(f'Client returns error "{resp.status_code} {error}"')

        result = data.get('data')

        return result


def _get_auth_token(username, password):
    if not username or not password:
        return ''

    sign_in_url = 'https://www.tradingview.com/accounts/signin/'

    data = {'username': username, 'password': password, 'remember': 'on'}
    headers = {'Referer': 'https://www.tradingview.com'}
    resp = post(url=sign_in_url, data=data,
                headers=headers, timeout=60)

    auth_token = resp.json()['user']['auth_token']

    return auth_token


def _parse_bar_charts(ws, sessions_completed: Dict[str, bool]) -> pd.DataFrame:
    symbol_dict: Dict[str, pd.DataFrame] = {}
    s_dict: Dict[str, pd.DataFrame] = {}
    st_dict: Dict[str, pd.DataFrame] = {}

    while True:
        try:
            msgs = ws.recv()

            if re.findall(r'~m~\d+~m~~h~\d+', msgs):
                _send_ping_packet(ws, msgs)
                continue

            if not msgs or '"session_id"' in msgs:
                continue

            segments = filter(None, re.split(r'~m~\d+~m~', msgs))

            for segment in segments:
                _segment_data: Dict[str, Any]

                try:
                    _segment_data = json.loads(segment)
                except json.JSONDecodeError:
                    continue

                m = _segment_data.get('m')
                if m is None:
                    continue

                if 'error' in m:
                    raise ConnectionError(f'Client returns error "{m}", detail "{_segment_data}"')

                p = _segment_data['p']
                sess = p[0]

                if m in ['symbol_resolved']:
                    symbol_dict[sess] = p[2].get('pro_name')

                if m in ['series_completed', 'study_completed']:
                    sessions_completed.update({f'{sess}__{p[1]}': True})

                if m in ['timescale_update', 'du']:
                    series = next(iter(p[1]))

                    s = p[1][series].get('s')
                    st = p[1][series].get('st')

                    if s is not None:
                        _df = _parse_series(s)
                        _df_exist = s_dict.get(sess, pd.DataFrame())
                        # concat by 'index' or 'columns'
                        _axis = {True: 1, False: 0}[bool(set(_df.columns) - set(_df_exist.columns))]
                        s_dict[sess] = pd.concat([s_dict.get(sess), _df], axis=_axis)

                    if st is not None:
                        _df = _parse_study(st, name=series)
                        _df_exist = st_dict.get(sess, pd.DataFrame())
                        # concat by 'index' or 'columns'
                        _axis = {True: 1, False: 0}[bool(set(_df.columns) - set(_df_exist.columns))]
                        st_dict[sess] = pd.concat([st_dict.get(sess), _df], axis=_axis)

            if all(sessions_completed.values()):
                dfs: List[pd.DataFrame] = []
                for _sess, _symbol in symbol_dict.items():
                    s = s_dict.get(_sess)
                    st = st_dict.get(_sess)
                    _df = pd.concat([s, st], axis=1)
                    _df['symbol'] = [_symbol] * len(_df)
                    _df['symbol'] = _df.symbol.astype('string')
                    _df['session'] = [_sess] * len(_df)
                    _df['session'] = _df.session.astype('string')
                    dfs.append(_df)

                df = pd.concat(dfs, axis=0)

                return df
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("=========except", datetime.now(), e)
            if ('closed' in str(e) or 'lost' in str(e)):
                print("=========try")
                # self.realtime_bar_chart(5, 1, callback)
            break


def _socket_quote(ws: WebSocket,
                  symbols: Union[str, List[str]] = None,
                  realtime=False,
                  callback: callable = None) -> Union[None, dict]:
    '''
    timeout is 3 seconds per 1 symbols
    '''
    msg = {}
    timeout_per_symbol = 3
    t1 = perf_counter()

    while True:
        try:
            msgs = ws.recv()

            if re.findall(r'~m~\d+~m~~h~\d+', msgs):
                _send_ping_packet(ws, msgs)
                continue

            if not msgs or '"session_id"' in msgs:
                continue

            m_items = filter(None, re.split(r'~m~\d+~m~', msgs))
            m_items = list(m_items)

            m: str = None
            for i in m_items:
                data = {}
                m_data = json.loads(i)

                m = m_data.get('m')
                if not m:
                    continue

                p = m_data['p']
                sess = p[0]

                if 'error' in m:
                    raise ConnectionError(f'Client returns error "{m}", detail "{p[1]}"')

                if m == 'quote_completed':
                    data = {sess: {p[1]: {m: True}}}

                elif isinstance(p[1], dict) and p[1].get('s') == 'ok':
                    n = p[1]['n']
                    v = p[1]['v']

                    data = {sess: {n: v}}

                    if callback is not None:
                        callback({n: v})

                msg = deep_update(msg, data)

            if not realtime:
                _symbols = [symbols] if isinstance(symbols, str) else symbols
                sess = next(iter(msg.keys()))

                duration = perf_counter() - t1
                timeout = timeout_per_symbol * len(_symbols)
                is_timeout = duration > timeout
                if is_timeout:
                    raise TimeoutError(f'expect should be done within {timeout} seconds, actually over {duration}')

                quote_completed = all([v.get('quote_completed') for _, v in msg[sess].items()])
                enough_symbols = not set(_symbols) - set(msg[sess].keys())

                if enough_symbols and quote_completed:
                    _ = [v.pop('quote_completed', None) for _, v in msg[sess].items()]
                    break

        except KeyboardInterrupt:
            break
        except Exception as e:
            if not realtime:
                raise e

            print("=========except", datetime.now(), e)
            if ('closed' in str(e) or 'lost' in str(e)):
                print("=========try")

            time.sleep(30)

    return msg


def _generate_session(prefix):
    string_length = 12
    letters = string.ascii_lowercase
    random_string = ''.join(random.choice(letters) for i in range(string_length))
    return prefix + random_string


def _prepend_header(st):
    return '~m~' + str(len(st)) + '~m~' + st


def _construct_message(func, params):
    return json.dumps({'m': func, 'p': params}, separators=(',', ':'))


def _create_message(func, params):
    return _prepend_header(_construct_message(func, params))


def _send_message(ws, func, args):
    ws.send(_create_message(func, args))


def _send_ping_packet(ws, result):
    ping_str = re.findall('.......(.*)', result)
    if len(ping_str) != 0:
        ping_str = ping_str[0]
        ws.send('~m~' + str(len(ping_str)) + '~m~' + ping_str)


def _parse_series(data: List[Dict[str, Union[int, List[float]]]]) -> pd.DataFrame:
    df_raw = pd.DataFrame(data)
    df_raw = df_raw[df_raw.i > 0]
    df = pd.DataFrame(df_raw.v.to_list()).set_index(0).rename_axis('timestamp', axis=0)
    df.index = pd.to_datetime(df.index, unit='s', utc=True)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    return df


def _parse_study(data: List[Dict[str, Union[int, List[float]]]], name: str) -> pd.DataFrame:
    df_raw = pd.DataFrame(data)
    df_raw = df_raw[df_raw.i > 0]
    df = pd.DataFrame(df_raw.v.to_list()).set_index(0).rename_axis('timestamp', axis=0)
    df.index = pd.to_datetime(df.index, unit='s', utc=True)
    if len(df.columns) > 1:
        df.columns = [f'{name.removeprefix("s_")}_{i}' for i in df.columns]
    else:
        df.columns = [f'{name.removeprefix("s_")}']
    return df
