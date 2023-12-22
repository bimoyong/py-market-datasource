import pandas as pd
import pytz

TZ_CST = pytz.timezone('America/Chicago')
TZ_JST = pytz.timezone('Asia/Tokyo')


def set_index_by_timestamp(df: pd.DataFrame, tzinfo: pytz.BaseTzInfo = None) -> pd.DataFrame:
    if 'timestamp_ts' in df:
        df['timestamp'] = pd.to_datetime(df['timestamp_ts'], unit='s')

    if 'timestamp' in df:
        df = df.set_index('timestamp', drop=True)

    if tzinfo:
        df.index = df.index.tz_localize('UTC').tz_convert(tzinfo)

    return df
