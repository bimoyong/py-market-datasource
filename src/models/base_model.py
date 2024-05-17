from typing import Dict, List

from pydantic import BaseModel as Model


class BaseModel(Model):

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
