#!/usr/bin/python
# -*-coding: utf-8 -*-

# https://github.com/frictionlessdata/tableschema-py/tree/1d9750248de06a075029c1278404c5db5311fbc5/tableschema/types
# type and format

# Support types and formats:
# string
#   email
#   uri
#   uuid
#   ipv4
#   ipv6
#   hostname
#   datetime
# number
# integer
# boolean
#


import rfc3986
import re
import uuid
import datetime
import ipaddress
from pycsvschema import defaults


class TypeValidator(object):
    def __init__(self, field_schema):
        self.field_schema = field_schema
        self.format = self.field_schema.get('format', defaults.FIELDS_FORMAT)
        self.value = None
        self.to_type = None

    def try_convert_value(self, value, to_type, convertor_config=None, update=False):
        if not convertor_config:
            convertor_config = {}

        try:
            v = to_type(value, **convertor_config)
        except Exception:
            return False

        if update:
            self.value = v
        else:
            self.value = value
        return True

    def validate(self, value):
        pass


class StringValidator(TypeValidator):
    EMAIL_PATTERN = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    HOSTNAME_PATTERN = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*" \
                       r"([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"

    def __init__(self, field_schema):
        super().__init__(field_schema=field_schema)
        self.to_type = str
        self.pattern = ''

    def validate(self, value):
        if value is None:
            return

        self.value = value

        if self.format == 'email':
            if not re.match(self.EMAIL_PATTERN, value):
                return False
        elif self.format == 'uri':
            if not rfc3986.is_valid_uri(value, require_scheme=True):
                return False
        elif self.format == 'uuid':
            return self.try_convert_value(value=value, to_type=uuid.UUID, convertor_config={'version': 4})
        elif self.format == 'ipv4':
            return self.try_convert_value(value=value, to_type=ipaddress.IPv4Address)
        elif self.format == 'ipv6':
            return self.try_convert_value(value=value, to_type=ipaddress.IPv6Address)
        elif self.format == 'hostname':
            if not re.match(self.HOSTNAME_PATTERN, value):
                return False
        elif self.format == 'datetime':
            self.pattern = self.field_schema.get('pattern', defaults.FIELDS_FORMAT_DATETIME_PATTERN)
            try:
                datetime.datetime.strptime(value, self.pattern)
            except Exception:
                return False
        elif self.field_schema.get('pattern', defaults.FIELDS_TYPE_STRING_PATTERN):
            self.pattern = self.field_schema.get('pattern', defaults.FIELDS_TYPE_STRING_PATTERN)
            if not re.match(self.pattern, value):
                return False
        return True


class NumberValidator(TypeValidator):
    def __init__(self, field_schema):
        super().__init__(field_schema=field_schema)
        self.to_type = float
        self.groupchar = self.field_schema.get('groupChar', defaults.FIELDS_GROUPCHAR)

    def validate(self, value):
        if value is None:
            return

        value = value.replace(self.groupchar, '')
        return self.try_convert_value(value=value, to_type=self.to_type, update=True)


class IntegerValidator(TypeValidator):
    def __init__(self, field_schema):
        super().__init__(field_schema=field_schema)
        self.to_type = int
        self.groupchar = self.field_schema.get('groupChar', defaults.FIELDS_GROUPCHAR)

    def validate(self, value):
        if value is None:
            return

        value = value.replace(self.groupchar, '')
        return self.try_convert_value(value=value, to_type=self.to_type, update=True)


class BooleanValidator(TypeValidator):
    def __init__(self, field_schema):
        super().__init__(field_schema=field_schema)
        self.to_type = bool
        self.truevalues = self.field_schema.get('trueValues', defaults.FIELDS_TRUEVALUES)
        self.falsevalues = self.field_schema.get('falseValues', defaults.FIELDS_FALSEVALUES)

    def validate(self, value):
        if value in self.truevalues:
            self.value = True
        elif value in self.falsevalues:
            self.value = False
        else:
            return False
        return True


TYPE_MAPPER = {
    'string': StringValidator,
    'number': NumberValidator,
    'integer': IntegerValidator,
    'boolean': BooleanValidator,
}
