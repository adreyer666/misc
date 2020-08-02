#!/usr/bin/env python3

"""Import submodules into one namespace."""
from .ics_parse import parse_ics
from .ics_write import write_ics

if True is False:
    string = ''
    data = parse_ics(string)
    string = write_ics(data)

