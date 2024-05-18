import json

import pandas as pd
from google import auth
from google.cloud.bigquery import Client as BigQueryClient
from google.cloud.bigquery import SqlTypeNames, StandardSqlTypeNames, Table

credentials, _ = auth.default()


def frame_to_big_query(data: pd.DataFrame, table_name: str) -> dict:
    rst: dict = None

    with BigQueryClient(credentials=credentials) as bq_client:
        table = bq_client.get_table(table_name)
        db_fields = [i.name for i in table.schema]
        data_fields = [i for i in data
                       if i in db_fields or i.lower() in db_fields]

        _data = data[data_fields].copy()
        _data.columns = [i.lower() for i in _data.columns]
        _data = cast_db_field_type(_data, table)

        rst = bq_client.insert_rows_from_dataframe(table, _data)

    return rst


def cast_db_field_type(data: pd.DataFrame,
                       table: Table) -> pd.DataFrame:
    for field in table.schema:
        if field.name not in data:
            continue

        if field.mode == 'REPEATED' or \
            field.field_type in [StandardSqlTypeNames.ARRAY,
                                 StandardSqlTypeNames.STRUCT,
                                 StandardSqlTypeNames.JSON]:
            data.loc[:, field.name] = data[field.name].apply(lambda x: eval(x) if isinstance(x, str) else x)

            if field.field_type in [StandardSqlTypeNames.JSON]:
                data.loc[:, field.name] = data[field.name].apply(lambda x: json.dumps(x) if x is not None else x)

        else:

            if field.field_type == SqlTypeNames.INTEGER:
                data.loc[:, field.name] = data[field.name].apply(lambda x: int(x) if x is not None else x)

            if field.field_type == SqlTypeNames.BOOL:
                data.loc[:, field.name] = data[field.name].apply(lambda x: bool(x) if x is not None else x)

            if field.field_type == SqlTypeNames.FLOAT:
                data.loc[:, field.name] = data[field.name].apply(lambda x: float(x) if x is not None else x)

            if field.field_type == SqlTypeNames.STRING:
                data.loc[:, field.name] = data[field.name].apply(lambda x: str(x) if x is not None else x)

            if field.field_type == SqlTypeNames.TIMESTAMP:
                data.loc[:, field.name] = pd.to_datetime(data[field.name])

    return data
