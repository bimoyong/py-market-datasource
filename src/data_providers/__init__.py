# -*- coding: utf-8 -*-

from logging import INFO, basicConfig
from sys import stdout

from data_providers.containers import Container
from data_providers.data_provider import DataProvider
from data_providers.enums import *
from data_providers.models import *

basicConfig(
    level=INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    stream=stdout,
)
