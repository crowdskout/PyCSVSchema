#!/usr/bin/python
# -*-coding: utf-8 -*-

import csv
from itertools import chain
import json
import jsonschema
from pycsvschema.validators import header_validators
from pycsvschema import defaults, _utilities
import asyncio


class Validator:
    _CSV_DEFAULT_PARS = {
        'delimiter': ',',
        'doublequote': True,
        'escapechar': None,
        'lineterminator': '\r\n',
        'quotechar': '"',
        'quoting': csv.QUOTE_MINIMAL,
        'skipinitialspace': False,
        'strict': False
    }

    def __init__(self, schema, filename, output=None, errors='raise', **kwargs):
        """

        :param schema:
        :type schema: dict
        """
        self.schema = schema

        self.filename = filename

        self.header = []

        self.output = output

        if errors not in {'raise', 'coerce'}:
            raise ValueError("Unknown value for parameter errors")
        self.errors = errors
        
        self.csv_pars = {
            **self._CSV_DEFAULT_PARS,
            **{k: kwargs[k] for k in set(kwargs).intersection(self._CSV_DEFAULT_PARS)}
        }

        self.column_validators = {
            'columns': {},
            'unfoundfields': {}
        }

        self.validate_schema()

        self.update_schema()

    def validate_schema(self):
        meta_schema = json.load(open('pycsvschema/schema.json', 'r'))
        jsonschema.validate(self.schema, meta_schema)

    def update_schema(self):
        # Convert list in schema into set
        # missingValues
        if 'missingValues' not in self.schema.keys():
            self.schema['missingValues'] = defaults.MISSINGVALUES
        self.schema['missingValues'] = set(self.schema['missingValues'])

    def validate(self):
        with open(self.filename, 'r') as csvfile:
            csv_reader = csv.reader(csvfile, **self.csv_pars)

            # Read first line as header
            self.header = next(csv_reader)
            self.prepare_field_schema()

            with _utilities.file_writer(self.output) as output:
                # Concat errors from header checking and row checking
                for error in chain(self.check_header(), self.check_rows(csv_reader)):
                    if self.errors == 'raise':
                        raise error
                    else:
                        output.write(str(error))
                        output.write('\n')

    def prepare_field_schema(self):
        """
        Prepare validators from `fields` option for every column

        Sample self.column_validators
        {
            'columns':{
                0: {
                    'column': '<COLUMN_NAME>',
                    'field_schema': {'name':'id', 'type': 'number'},
                    'validators': [
                        < function csvchecker._validators.validate_type >,
                        < function csvchecker._validators.validate_type >
                    ],
                    'patternfields': {
                        '<PATTERN>': {
                            'field_schema': {'name':'id', 'type': 'number'},
                            'column': '<COLUMN_NAME>'
                        }
                    }
                }
            },
            'unfoundfields': {
                '<FIELD_NAME>': {
                    'field_schema': {'name':'id', 'type': 'number'},
                    'column': '<COLUMN_NAME>'
                }
            },
            'definitions': {
                'ref1': {
                    'validators': [
                        < function csvchecker._validators.validate_type >,
                        < function csvchecker._validators.validate_type >
                    ],
                    'field_schema': {'name':'id', 'type': 'number'}
                }
            },
            'patternfields': {
                'ref1': {
                    'validators': [
                        < function csvchecker._validators.validate_type >,
                        < function csvchecker._validators.validate_type >
                    ],
                    'field_schema': {'name':'id', 'type': 'number'}
                }
            }
        }
        """

        # Sample header_index {'col_1': [0, 1],}
        # column names might not be unique
        header_index = {}
        for k, v in enumerate(self.header):
            if v in header_index:
                header_index[v].append(k)
            else:
                header_index[v] = [k]

        for field_schema in self.schema.get('fields', defaults.FIELDS):
            column_info = {
                'field_schema': field_schema,
                'column': field_schema['name']
            }

            _utilities.find_row_validators(column_info=column_info, field_schema=field_schema)

            # Pass the validators to one or more than one columns
            if field_schema['name'] in header_index.keys():
                for column_index in header_index[field_schema['name']]:
                    self.column_validators['columns'][column_index] = column_info
            # Store the unfound field names in column_validators.unfoundfields
            else:
                self.column_validators['unfoundfields'][field_schema['name']] = column_info

    def check_header(self):
        for validator_name, validator in header_validators.HEADER_OPTIONS.items():
            if validator_name in self.schema:
                yield from validator(self.header, self.schema, self.column_validators)

        yield from header_validators.field_required(self.header, self.schema, self.column_validators)

    def check_rows(self, csvreader):
        for line_num, row in enumerate(csvreader):
            for index, column_info in self.column_validators['columns'].items():
                c = {'value': row[index], 'row': line_num + 1, 'column': self.header[index]}

                # Update c.value to None if value is in missingValues
                yield from header_validators.missingvalues(c, self.schema, self.column_validators)

                for validator in column_info['validators']:
                    # Type validator convert cell value into target type, other validators don't accept None value
                    # if validator is row_validators.field_type or c['value'] is not None:
                    yield from validator(c, self.schema, column_info['field_schema'])


class AsyncValidator(Validator):
    def __init__(self, schema, filename, chunksize, **kwargs):
        super().__init__(schema, filename, **kwargs)
        self.chunksize = chunksize

    async def check_rows(self, csvreader):
        # split csv into
        # [(1, [row_1,..]), (2, [row_2,..]),..,(chunksize, [row_chunksize,])], ...
        for chunk in _utilities.step_slice(enumerate(csvreader), self.chunksize):
            coros = [self._check_row(row, line_num) for line_num, row in chunk]
            for future in asyncio.as_completed(coros):
                yield await future

    async def _check_row(self, row, row_num):
        future = asyncio.Future()
        result = []
        for index, column_info in self.column_validators['columns'].items():
            c = {'value': row[index], 'row': row_num + 1, 'column': self.header[index]}

            # Update c.value to None if value is in missingValues
            for error in header_validators.missingvalues(c, self.schema, self.column_validators):
                result.append(error)

            for validator in column_info['validators']:
                # Type validator convert cell value into target type, other validators don't accept None value
                # if validator is row_validators.field_type or c['value'] is not None:
                for error in validator(c, self.schema, column_info['field_schema']):
                    result.append(error)
        future.set_result(result)
        return future

    async def row_error_consumer(self, output, errors):
        async for error in errors:
            for r in error.result():
                if self.errors == 'raise':
                    raise r
                else:
                    output.write(str(r))
                    output.write('\n')

    def validate(self):
        self.validate_schema()

        with open(self.filename, 'r') as csvfile:
            csv_reader = csv.reader(csvfile, **self.csv_pars)

            # Read first line as header
            self.header = next(csv_reader)
            self.prepare_field_schema()

            with _utilities.file_writer(self.output) as output:
                # Concat errors from header checking and row checking
                for error in chain(self.check_header()):
                    if self.errors == 'raise':
                        raise error
                    else:
                        output.write(str(error))
                        output.write('\n')

                self.async_check_row(output, csv_reader)

    def async_check_row(self, output, csv_reader):
        main = self.row_error_consumer(output, self.check_rows(csv_reader))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main)
        loop.close()
