import json
import logging
import re
import subprocess
import sys
import unittest
import warnings
from contextlib import suppress
from logging import StreamHandler
from os import chdir
from os.path import join
from subprocess import CalledProcessError

import pandas as pd
from dependency_injector import providers
from pydantic.utils import deep_update

with suppress(CalledProcessError):
    WORKING_DIR = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip().decode()
    sys.path.extend([WORKING_DIR, join(WORKING_DIR, 'src')])
    chdir(WORKING_DIR)

from src.data_providers.containers import Container
from src.data_providers.tradingview import Quote, TradingView

warnings.filterwarnings('ignore')
pd.options.display.float_format = '{:,.4f}'.format


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(StreamHandler())


class TestTradingView(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.container = Container()
        self.container.client.override(providers.Singleton(TradingView))
        self.client = self.container.client()

    def test_get_current_quotes_good_connection(self):
        symbol = 'NASDAQ:MSFT'
        symbols = ['NASDAQ:MSFT', 'NASDAQ:QQQ']

        quote = self.client.quotes(symbol)
        quotes = self.client.quotes(symbols)

        self.assertTrue(quote.symbol, symbol)
        list(map(lambda x: self.assertIn(x, symbols), quotes.keys()))

    def test_get_current_quotes_return_type(self):
        symbol = 'NASDAQ:MSFT'
        symbols = ['NASDAQ:MSFT', 'NASDAQ:QQQ']

        quote = self.client.quotes(symbol)
        quotes = self.client.quotes(symbols)

        self.assertIsInstance(quote, Quote)

        self.assertIsInstance(quotes, dict)
        list(map(lambda x: self.assertIsInstance(x, Quote), quotes.values()))
        list(map(lambda x: self.assertIsInstance(x, str), quotes.keys()))

    def test_get_current_quotes_require_fields(self):
        symbol = 'NASDAQ:MSFT'
        symbols = ['NASDAQ:MSFT', 'NASDAQ:QQQ']

        quote = self.client.quotes(symbol)
        quotes = self.client.quotes(symbols)

        for q in [quote, *quotes.values()]:
            q: Quote
            self.assertIsNotNone(q.price)
            self.assertIsNotNone(q.change)
            self.assertIsNotNone(q.timestamp_ts)
            self.assertIsNotNone(q.change_pct)
            self.assertIsNotNone(q.volume)

    def test_split(self):
        with open('src/test/fixtures/NASDAQ:QQQ_analysis.csv') as msgs:
            msg = {}

            for m in msgs:
                m_items = filter(None, re.split('~m~\d+~m~', m))

                for i in m_items:
                    m_data = json.loads(i)

                    m = m_data.get('m')
                    if not m:
                        continue

                    if m == 'quote_completed':
                        break

                    p = m_data['p']
                    s = p[1]['s']
                    if s != 'ok':
                        continue

                    n = p[1]['n']
                    v = p[1]['v']

                    sess = p[0]
                    data = {sess: {n: v}}

                    msg = deep_update(msg, data)
