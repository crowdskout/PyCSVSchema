# PyCSVSchema

PyCSVSchema is an implementation of [CSV Schema](https://github.com/csvschema/csvschema) in Python.

This project is under heavy development.

```python
>>> from pycsvschema.checker import Validator
>>> 
>>> # demo.csv:
... # id,name,value
... # 1,Ann,"5"
... # 2,Ben,"10"
... # 3,Tom,"14"
... 
>>> 
>>> schema = {
...     'fields': [
...         {
...             'name': 'value',
...             'type': 'number',
...             'multipleOf': 5
...         }
...     ]
... }
>>> 
>>> v = Validator(filename='demo.csv', schema=schema)
>>> v.validate()

Traceback (most recent call last):
...
<ValidationError: 'Value 14.0 is not multiple of 5'; column: value; row: 3>
```

## Installation

```bash
pip install pycsvschema
```

## Requirements

Python 3.5 or above


## TODO
* tests