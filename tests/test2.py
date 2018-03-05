#!/usr/bin/python
# -*-coding: utf-8 -*-

from pycsvschema.checker import Validator, AsyncValidator
schema = {
    'fields': [
        {
            'name': 'messages_created_date',
            'type': 'string',
            'format': 'datetime',
            'pattern': '%Y-%m-%d'
        },
        {
            'name': 'agents_phone_number',
            'type': 'string',
            'pattern': '\+1\d{10}',
            'maxLength': 15
        },
        {
            'name': 'messages_is_from_agent',
            'type': 'string',
            'enum': ['Yes', 'No'],
            'pattern': '[Yes|No]',
            'maxLength': 3
        },
        {
            'name': 'leads_email',
            '$ref': 'e-mail',
        },
        {
            'name': 'agents_email',
            '$ref': 'e-mail',
        },
    ],
    "definitions": {
        "e-mail": {
            "type": "string",
            "format": "email",
            "required": True,
            'maxLength': 30
        }
    },
    "patternFields": {
        ".*_name$": {
            "type": "string",
            "maxLength": 50,
            "required": True
        }
    },
}

from datetime import datetime

start=datetime.now()
v = Validator(schema=schema, filename='message.csv', output='result', errors='coerce')
v.validate()
# v = AsyncValidator(filename='/Users/ligyxy/message.csv', output='result', errors='coerce', schema=schema, chunksize=100)
# v.validate()

print(datetime.now()-start)