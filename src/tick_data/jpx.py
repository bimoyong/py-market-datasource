import json
from datetime import datetime, timedelta
from logging import INFO, StreamHandler, getLogger
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd
from dateutil.parser import parse as date_parse
from google.cloud.storage import Client as StorageClient
from requests import Session, post
from tqdm import tqdm

from infra.big_query import credentials
from tick_data.provider import TickDataProvider

logger = getLogger(__name__)
logger.setLevel(INFO)
logger.addHandler(StreamHandler())


class JPX(TickDataProvider):

    GCS_BUCKET_NAME: str = None

    def fetch_token(self) -> Dict[str, Any]:
        url = f'{self.BASE_URL}/user_admin/auth/login'

        headers = {
            'Content-Type': 'application/json',
        }

        payload = json.dumps({
            'userName': self.USERNAME,
            'password': self.PASSWORD,
        })

        resp = post(url, data=payload, headers=headers, timeout=5)

        data = resp.json()

        return {
            'access_token': data.get('idToken'),
            'refresh_token': data.get('refreshToken'),
        }

    def list_files(self,
                   from_date: datetime = None,
                   to_date: datetime = None) -> pd.DataFrame:
        # because there is concurrency in this function, so token should be initialized
        _ = self.access_token

        if to_date is None:
            to_date = datetime.now()

        if from_date is None:
            from_date = to_date - timedelta(days=365)

        days_delta = abs((to_date - from_date).days)

        dates: List[datetime] = []
        for i in range(days_delta):
            _date = from_date + timedelta(days=i)
            dates.append(_date)

        def get_single_list(date: datetime) -> pd.DataFrame:
            _url = f'{self.BASE_URL}/flex/list_date'

            _headers = {
                'Content-Type': 'application/json',
                'Authorization': self.access_token,
            }

            _payload = json.dumps({
                'getDate': date.strftime('%Y%m%d'),
            })

            _resp = post(_url, data=_payload, headers=_headers, timeout=5)

            if _resp.status_code == 401:
                self._token_cache.clear()
                return get_single_list(date=date)

            if _resp.status_code == 400:
                return None

            if _resp.status_code != 200:
                raise ConnectionRefusedError(
                    f'Unknown JPX error {_resp.status_code} {_resp.text}')

            _data = _resp.json()

            _df = pd.DataFrame(_data.get('lists', []))
            _df['date'] = date.strftime('%Y%m%d')
            _df.set_index(['date', 'no'], drop=True, inplace=True)

            _df['file_name'] = _df['path'].apply(
                lambda x: x.split('/')[-1]).astype(str)
            _df['size_bytes'] = _df['size'].str.replace(',', '').astype(int)

            return _df

        df_ls = self.executor.map(get_single_list, dates)

        df = pd.concat(df_ls, axis=0)

        return df

    def download_files_background(self,
                                  workers_no: int = 4) -> None:
        # because there is concurrency in this function, so token should be initialized
        _ = self.access_token

        df = pd.read_csv('test/fixtures/jpx_list_downloads_20230401_20240531.csv',
                         index_col='index')

        df_undone = df.loc[df['gcp_gcs_path'].isnull() & df['error'].isnull()]
        if df_undone.empty:
            return 'done'

        batches = np.array_split(df_undone.index, len(df_undone) / workers_no)
        for idxes in tqdm(batches, total=len(batches)):
            _df = df.loc[idxes, ['file_name', 'size_bytes']]

            logger.info('Download file index %s', list(_df.index))

            rst = self.download_file(filenames=list(_df['file_name']),
                                     sizes=list(_df['size_bytes']))

            df.loc[idxes, ['gcp_gcs_path', 'error']] = pd.DataFrame(rst,
                                                                    index=_df.index,
                                                                    columns=['gcp_gcs_path', 'error'])

            df.to_csv('test/fixtures/jpx_list_downloads_20230401_20240531.csv')

    def download_file(self,
                      filenames: Union[str, List[str]],
                      sizes: Union[List[int], int] = None,
                      force=False) -> List[Tuple[str, str]]:
        # because there is concurrency in this function, so token should be initialized
        _ = self.access_token

        logger.info('Start download file list %s', filenames)

        if isinstance(filenames, str):
            filenames = [filenames]

        if isinstance(sizes, str):
            sizes = [sizes]

        if sizes is not None:
            if len(filenames) != len(sizes):
                raise ValueError(f'filenames and sizes should have the same length {len(filenames)} != {len(sizes)}')

        def download_file_to_gcs(filename: str, size: int = None) -> Tuple[str, str]:
            date_path = date_parse(filename.split('_')[0]).strftime('%Y/%m/%d')
            path = f'dataservice-flex-bucket/{date_path}/{filename}'

            _client = StorageClient(credentials=credentials)
            _bucket = _client.bucket(self.GCS_BUCKET_NAME)

            # ignore if file exists already and file size is sufficient
            if not force:
                _blob = _bucket.get_blob(path)
                if _blob and (size is None or _blob.size == size):
                    logger.info('Ignore downloading because file %s exists', filename)
                    return _blob.name, None

            info: Dict[str, str] = None
            try:
                info = self._get_file(filename=filename)
            except ConnectionRefusedError as error:
                logger.error('JPX does not allow download this file %s', filename)
                return None, str(error)

            path = info.get('path')
            url = info.get('url')

            # ignore if file exists already and file size is sufficient
            if not force:
                _blob = _bucket.get_blob(path)
                if _blob and (size is None or _blob.size == size):
                    logger.info('Ignore downloading because file %s exists', filename)
                    return _blob.name, None

            _blob = _bucket.blob(path)

            with Session() as _sess:
                _resp = _sess.get(url, stream=True)
                _blob.upload_from_string(_resp.content,
                                        content_type=_resp.headers['Content-Type'])

                logger.info('Download file %s done', filename)

                _client.close()

            return _blob.name, None

        if sizes is None:
            rst = list(tqdm(self.executor.map(download_file_to_gcs, filenames), total=len(filenames)))
        else:
            rst = list(tqdm(self.executor.map(download_file_to_gcs, filenames, sizes), total=len(filenames)))

        return rst

    def _get_file(self, filename: str) -> None:
        url = f'{self.BASE_URL}/flex/download'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.access_token,
        }

        payload = json.dumps({
            'fileName': filename,
            'getDate': filename.split('_')[0],
        })

        resp = post(url, data=payload, headers=headers, timeout=5)

        if resp.status_code == 401:
            self._token_cache.clear()
            return self._get_file(filename=filename)

        if resp.status_code == 400:
            raise ConnectionRefusedError(
                f'JPX error {resp.status_code} {resp.text}')

        if resp.status_code != 200:
            raise ConnectionRefusedError(
                f'Unknown JPX error {resp.status_code} {resp.text}')

        return resp.json()
