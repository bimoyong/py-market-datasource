from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field


class BaseQuote(BaseModel):
    symbol: Union[str, None] = None
    price: Union[float, None] = Field(serialization_alias='price', alias='lp', default=None)
    change: Union[float, None] = Field(serialization_alias='change', alias='ch', default=None)
    change_pct: Union[float, None] = Field(serialization_alias='change_pct', alias='chp', default=None)
    volume: Union[int, None] = None
    timestamp_ts: Union[int, None] = Field(serialization_alias='timestamp_ts', alias='lp_time', default=None)

    @classmethod
    def fields_map(cls) -> Dict[str, str]:
        '''
        This method returns dictionary of differences between class fields and provider's fields
        '''
        fields_map = {k: v.alias for k, v in cls.model_fields.items()
                      if v.alias and v.alias != k}

        return fields_map

    @classmethod
    def non_extra_keys(cls) -> List[str]:
        '''
        This method returns list of fields name which is preserved; other fields should be in "extra" attribute
        '''
        keys = cls.model_fields.keys()
        aliases = [v.alias for _, v in cls.model_fields.items() if v.alias]
        return list(set([*keys, *aliases]))


class Quote(BaseQuote):
    country_code: Union[str, None] = None
    logoid: Union[str, None] = None
    short_name: Union[str, None] = None
    pro_name: Union[str, None] = None
    currency_id: Union[str, None] = None
    type: Union[str, None] = None
    source_logoid: Union[str, None] = Field(serialization_alias='source_logoid', alias='source-logoid', default=None)
    description: Union[str, None] = None
    current_session: Union[str, None] = None

    logo_url: Union[str, None] = None
    source_logo_url: Union[str, None] = None

    extra: Dict[str, Any] = None
