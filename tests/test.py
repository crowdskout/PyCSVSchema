#!/usr/bin/python
# -*-coding: utf-8 -*-

from pycsvschema.checker import Validator, AsyncValidator

"""
CSV data:

id,name,numerical
1,n,"5"
2,a,"10"
3,m,"14"

"""

schema = {
    'fields': [
        {
            'name': 'id',
            'type': 'number',
            'maximum': 5,
            'required': True
        },
        {
            'name': 'numerical',
            'type': 'number',
            'multipleOf': 5
        }
    ],
    'dependencies': {
        'numerical': ['name']
    },
}

# v = Validator(filename='/Users/ligyxy/test.csv', schema=schema)
# v.validate()

v = AsyncValidator(filename='/Users/ligyxy/test.csv', schema=schema, chunksize=2)
v.validate()