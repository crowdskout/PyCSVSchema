#!/usr/bin/python
# -*-coding: utf-8 -*-

from pycsvschema import exceptions
from pycsvschema import defaults
from pycsvschema.validators import types

# Validators for options under `fields`
# Each validator should be a generator, accepting three parameters:
# :param cell: Cell
# :param schema: full csv schema
# :param field_schema: related option object under `fields`


def field_type(cell, schema, field_schema):
    # type is default validator and fields.type could be empty, so it has default value
    # type validator must run before other field validators (excluding $ref), since it transforms the value type in cell
    type_name = field_schema.get('type', defaults.FIELDS_TYPE)

    mapper = types.TYPE_MAPPER[type_name](field_schema=field_schema)
    if mapper.validate(value=cell['value']) is False:
        yield exceptions.ValidationError(
            message="Value {0} does not satisfy the type or format".format(cell['value']),
            column=field_schema.get('name'),
            row=cell['row']
        )
    cell['value'] = mapper.value
    # TODO: do we need type?
    # cell['dtype'] = mapper.to_type


def field_enum(cell, schema, field_schema):
    enum = field_schema['enum']

    failed = cell['value'] not in enum

    if failed:
        yield exceptions.ValidationError(
            message="Value {0} is not in enum of {1}".format(cell['value'], enum),
            column=field_schema.get('name'),
            row=cell['row']
        )


def field_maximum(cell, schema, field_schema):
    if cell['value'] is None:
        return

    maximum = field_schema['maximum']
    exclusivemaximum = field_schema.get('exclusiveMaximum', defaults.FIELDS_EXCLUSIVEMAXIMUM)

    if exclusivemaximum:
        failed = maximum < cell['value']
        comapre = "greater than or equal to"
    else:
        failed = maximum <= cell['value']
        comapre = "greater than"

    if failed:
        yield exceptions.ValidationError(
            message="Value {0} is {1} maximum of {2}".format(cell['value'], comapre, maximum),
            column=field_schema.get('name'),
            row=cell['row']
        )


def field_minimum(cell, schema, field_schema):
    if cell['value'] is None:
        return

    minimum = field_schema['minimum']
    exclusiveminimum = field_schema.get('exclusiveMinimum', defaults.FIELDS_EXCLUSIVEMININUM)

    if exclusiveminimum:
        failed = minimum > cell['value']
        comapre = "less than or equal to"
    else:
        failed = minimum >= cell['value']
        comapre = "less than"

    if failed:
        yield exceptions.ValidationError(
            message="Value {0} is {1} minimum of {2}".format(cell['value'], comapre, minimum),
            column=field_schema.get('name'),
            row=cell['row']
        )


def field_maxlength(cell, schema, field_schema):
    if cell['value'] is None:
        return

    maxlength = field_schema['maxLength']

    failed = maxlength < len(cell['value'])

    if failed:
        yield exceptions.ValidationError(
            message="Value {0} is longer than maxLength of {1}".format(cell['value'], maxlength),
            column=field_schema.get('name'),
            row=cell['row']
        )


def field_minlength(cell, schema, field_schema):
    if cell['value'] is None:
        return

    minlength = field_schema['minLength']

    failed = minlength > len(cell['value'])

    if failed:
        yield exceptions.ValidationError(
            message="Value {0} is shorter than minLength of {1}".format(cell['value'], minlength),
            column=field_schema.get('name'),
            row=cell['row']
        )


def field_multipleof(cell, schema, field_schema):
    if cell['value'] is None:
        return

    multipleof = field_schema['multipleOf']

    failed = cell['value'] % multipleof != 0

    if failed:
        yield exceptions.ValidationError(
            message="Value {0} is not multiple of {1}".format(cell['value'], multipleof),
            column=field_schema.get('name'),
            row=cell['row']
        )


def field_nullable(cell, schema, field_schema):
    if field_schema['nullable'] is True:
        return

    failed = cell['value'] is None

    if failed:
        yield exceptions.ValidationError(message="Illegal null value", column=field_schema.get('name'), row=cell['row'])


def field_ref(cell, schema, field_schema):
    """
    $ref keyword is handled by definitions
    """
    pass


ROW_OPTIONS = {
    # 'type': field_type,  # always run type check before other field options
    'enum': field_enum,
    'maximum': field_maximum,
    'minimum': field_minimum,
    'maxLength': field_maxlength,
    'minLength': field_minlength,
    'multipleOf': field_multipleof,
    'nullable': field_nullable,
    '$ref': field_ref,
}

# Other dependent options in fields:
#     format
#     pattern
#     trueValues
#     falseValues
#     groupChar
#     exclusiveMinimum
#     exclusiveMaximum
