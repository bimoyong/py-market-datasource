# @title ##Spreadsheet Utils

from contextlib import suppress
from google.auth.credentials import Credentials
from gspread import Spreadsheet, Worksheet
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread.exceptions import CellNotFound, SpreadsheetNotFound, WorksheetNotFound
from pandas.api.types import is_datetime64_ns_dtype
from typing import Any, Dict, Tuple
import gspread
import pandas as pd

WORKSHEET_TEMPLATE_TITLE = '_template'


class GoogleSheet():
    def __init__(self, credentials: Credentials) -> None:
        self._client = gspread.authorize(credentials)

    def open_or_create_spreadsheet(self, title: str) -> Spreadsheet:
        sh: Spreadsheet = None

        with suppress(SpreadsheetNotFound):
            sh = self._client.open(title)

        if not sh:
            sh = self._client.create(title)

        return sh

    @staticmethod
    def get_or_add_worksheet(title: str,
                             sheet: Spreadsheet,
                             template_data_range='') -> Worksheet:
        ws: Worksheet = None

        ws_template: Worksheet = None
        if template_data_range:
            with suppress(WorksheetNotFound):
                ws_template = sheet.worksheet(WORKSHEET_TEMPLATE_TITLE)

        ws: Spreadsheet = None
        with suppress(WorksheetNotFound):
            ws = sheet.worksheet(title)

        if not ws:
            if ws_template:
                ws = ws_template.duplicate(insert_sheet_index=1, new_sheet_name=title)
                ws.batch_clear([template_data_range])
            else:
                ws = sheet.add_worksheet(title, rows=0, cols=0)

        __class__.unhide_worksheet(ws, sheet)

        return ws

    @staticmethod
    def unhide_worksheet(worksheet: Worksheet,
                         sheet: Spreadsheet) -> Dict[str, Any]:
        resp = sheet.batch_update(body={
            'requests': [
                {'updateSheetProperties': {
                    'properties': {
                        'sheetId': worksheet.id,
                        'hidden': False
                    },
                    'fields': 'hidden'
                }}
            ]
        })

        return resp

    @staticmethod
    def dataframe_to_worksheet(df: pd.DataFrame,
                               worksheet: Worksheet,
                               include_index=True,
                               include_header=True,
                               row=1,
                               col=1):
        df_ws = df.copy()

        if not df_ws.index.name and is_datetime64_ns_dtype(df_ws.index):
            df_ws.index.name = 'timestamp'

        set_with_dataframe(worksheet,
                           df_ws,
                           include_index=include_index,
                           include_column_header=include_header,
                           row=row,
                           col=col)

    @staticmethod
    def worksheet_to_dataframe(worksheet: Worksheet,
                               row=1,
                               index='') -> Tuple[pd.DataFrame, int]:
        row_idx = row
        if index:
            with suppress(CellNotFound, AttributeError):
                row_idx = worksheet.find(index).row

        def skip(x):
            not_header = x != row - 1
            to_index = x < row_idx - 1

            if not_header and to_index:
                return True

        df_ws = get_as_dataframe(worksheet, parse_dates=True, index_col='timestamp', skiprows=skip)
        df_ws = df_ws.dropna(how='all', axis=0).dropna(how='all', axis=1)

        row_last = {True: len(df_ws) + 1, False: row_idx}[row_idx == row]

        return df_ws, row_last
