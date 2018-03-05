#!/usr/bin/python
# -*-coding: utf-8 -*-


class ValidationError(Exception):
    def __init__(self, message, column=None, row=None, *args):
        self.message = message
        self.column = column
        self.row = row

        super(ValidationError, self).__init__(message, column, row, *args)

    def __str__(self):
        return "<%s: %r; column: %s; row: %s>" % (self.__class__.__name__, self.message, self.column, self.row)
