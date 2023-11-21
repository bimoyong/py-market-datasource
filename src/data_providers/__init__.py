# -*- coding: utf-8 -*-

from logging import INFO, basicConfig
from sys import stdout

from data_providers.data_providers import DataProvider

basicConfig(
    level=INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    stream=stdout,
)
