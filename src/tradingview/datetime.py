import pandas as pd
import pytz

TZ_CST = pytz.timezone('America/Chicago')
TZ_JST = pytz.timezone('Asia/Tokyo')


def set_index_by_timestamp(df: pd.DataFrame,
                           tzinfo: pytz.BaseTzInfo = None) -> pd.DataFrame:
    _df = df.copy()

    if 'timestamp_ts' in _df:
        _df['timestamp'] = pd.to_datetime(_df['timestamp_ts'], unit='s')

    if 'timestamp' in _df:
        _df = _df.set_index('timestamp', drop=True)

    if tzinfo:
        index_names = _df.index.names
        _df.reset_index(inplace=True)
        _df['timestamp'] = _df['timestamp'].apply(lambda x: x.tz_localize('UTC') if x.tz is None else x).dt.tz_convert(tzinfo)
        _df.set_index(index_names, inplace=True)

    return _df
