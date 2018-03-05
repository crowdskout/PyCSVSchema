#!/usr/bin/python
# -*-coding: utf-8 -*-

from itertools import chain
import re
from pycsvschema import exceptions
from pycsvschema import defaults, _utilities


# Validators for root options
# Each validator should be a generator, accepting three parameters:
# :param header: csv header
# :param cell: cell data in dict like {'value': 1}, only for missingvalues
# :param schema: full csv schema
# :param column_validators: Validator.column_validators


def additionalfields(header, schema, column_validators):
    if schema['additionalFields'] is True:
        return

    extra_fields = set(header) - set(field.get('name') for field in schema.get('fields', defaults.FIELDS))
    for extra_field in extra_fields:
        matched = False
        for regex in schema.get('patternFields', defaults.PATTERNFIELDS).keys():
            if re.match(regex, extra_field):
                matched = True
        if matched is False:
            yield exceptions.ValidationError(
                message="Field {0} is not defined".format(extra_field)
            )


def definitions(header, schema, column_validators):
    """
    definitions is not a validator, but only append schema in definitions to column_validators

    Update validators for all fields using $ref keyword

    This should be the last root validator
    """
    # Prepare schema in definitions and add it to column_validators
    column_validators['definitions'] = {}
    for ref_name, field_schema in schema['definitions'].items():
        column_info = {
            'field_schema': field_schema,
        }

        _utilities.find_row_validators(column_info=column_info, field_schema=field_schema)

        column_validators['definitions'][ref_name] = column_info

    for column_info in chain(column_validators['columns'].values(), column_validators['unfoundfields'].values()):
        if column_info.get('ref') is not None:
            if column_info['ref'] not in schema['definitions'].keys():
                raise ValueError("Referencing undefined field")

            column_info.update(column_validators['definitions'][column_info['ref']])

    yield from ()


def dependencies(header, schema, column_validators):
    for column, dependents in schema['dependencies'].items():
        if column not in header:
            continue
        for d in dependents:
            if d in header:
                continue
            yield exceptions.ValidationError(
                message="Field {0} is provided while {0} is not in header".format(column, d)
            )


def exactfields(header, schema, column_validators):
    """
    Redo the whole column_validators from fields by order,
    in order to pass validators to columns with same name correctly
    """
    if not schema['exactFields']:
        return

    failed = [field.get('name') for field in schema.get('fields', defaults.FIELDS)] != header

    if failed:
        yield exceptions.ValidationError(
            message="Column name is different to fields.name in schema"
        )

    column_validators['columns'].clear()
    for column_index, column in enumerate(header):
        field_schema = schema.get('fields', defaults.FIELDS)[column_index]

        column_info = {
            'field_schema': field_schema,
            'column': column
        }

        _utilities.find_row_validators(column_info=column_info, field_schema=field_schema)

        column_validators['columns'][column_index] = column_info


def maxfields(header, schema, column_validators):
    failed = len(header) > schema['maxFields']

    if failed:
        yield exceptions.ValidationError(
            message="Number of column(s) is greater than maxFields of {0}".format(schema['maxFields'])
        )


def minfields(header, schema, column_validators):
    failed = len(header) < schema['minFields']

    if failed:
        yield exceptions.ValidationError(
            message="Number of column(s) is less than minFields of {0}".format(schema['minFields'])
        )


def missingvalues(cell, schema, column_validators):
    """
    missingvalues is not a validator, but only cell value into None if it's in missing value list
    :param cell: cell data in dict like {'value': 1}, only for missingvalues
    """
    # TODO: DEFAULT_MISSINGVALUES would not be triggered here, how to apply it?
    if cell['value'] in schema.get('missingValues', defaults.MISSINGVALUES):
        cell['value'] = None
    yield from ()


def patternfields(header, schema, column_validators):
    """
    patternfields is not a validator, but append field schema in patternfields to column_validators
    """
    # If exactFields is True, ignore patternFields
    if schema.get('exactFields', defaults.EXACTFIELDS):
        return

    column_validators['patternfields'] = {}
    for pattern, field_schema in schema['patternFields'].items():
        column_info = {
            'field_schema': field_schema,
        }
        _utilities.find_row_validators(column_info=column_info, field_schema=field_schema)

        column_validators['patternfields'][pattern] = column_info

    for column_index, column in enumerate(header):
        # If it's defined in `fields` option, skip it
        if column_validators['columns'].get(column_index) is not None:
            continue

        for regex, column_info in column_validators['patternfields'].items():
            if not re.match(regex, column):
                continue

            new_column_info = {
                'column': column,
                'pattern': regex
            }

            new_column_info.update(column_info)

            column_validators['columns'][column_index] = new_column_info

            column_validators['unfoundfields'].pop(column, None)
            break

    yield from ()


def field_required(header, schema, column_validators):
    if schema.get('exactFields', defaults.EXACTFIELDS):
        return

    for column_info in column_validators['columns'].values():
        failed = column_info['field_schema'].get('required', defaults.FIELDS_REQUIRED) and column_info['column'] not in header
        if failed:
            yield exceptions.ValidationError(
                message="{0} is a required field".format(column_info['column'])
            )

    for column_name, column_info in column_validators['unfoundfields'].items():
        if column_info['field_schema'].get('required', defaults.FIELDS_REQUIRED):
            yield exceptions.ValidationError(
                message="{0} is a required field".format(column_info['column'])
            )


HEADER_OPTIONS = {
    'additionalFields': additionalfields,
    'dependencies': dependencies,
    'exactFields': exactfields,
    'maxFields': maxfields,
    'minFields': minfields,
    # 'missingValues': missingvalues,  # Run missingValues checking in row checking
    'patternFields': patternfields,
    'definitions': definitions
}
