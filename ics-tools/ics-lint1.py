#!/usr/bin/env python3

"""
Small application to fix ics files
"""

import os
import sys
import re
import json
from uuid import uuid4
from ics import parse_ics

verbose = 0


# --------- helper routines ----------- #


def getfiles(topdir) -> list:
    filelist = list()
    for root, dirs, files in os.walk(topdir, topdown=False):
        for name in files:
            filelist.append(os.path.join(root, name))
    return filelist


def readfile(file) -> str:
    """Read from file return contents or empty string."""
    if file:
        try:
            if os.stat(file):
                with open(file, 'r', encoding='utf8') as file_handle:
                    file_content = file_handle.read()
                return file_content
        except FileNotFoundError as err:
            if verbose > 1:
                print(err)
    return ''

def writefile(file, data=None) -> bool:
    """Write data to file, use empty string if no data provided."""
    if file:
        if data is None:
            data = ''
        try:
            with open(file, 'w', encoding='utf8') as file_handle:
                file_handle.write(data)
        except OSError as err:
            if verbose > 1:
                print(err)
            return False
    return True


def new_uuid() -> str:
    """Create new UUID as string."""
    uuid = str(uuid4())
    if verbose > 1:
        print("New UUID: ", uuid)
    return uuid


def main(taskdir) -> int:
    pattern = r'^\w+[\w-]+\w$'
    uidregex = re.compile(pattern)

    try:
        os.stat(taskdir)
    except FileNotFoundError as err:
        if verbose:
            print('Directory not found, exiting.')
        if verbose > 1:
            print(err)
        return 1

    for filename in getfiles(taskdir):
        if verbose:
            print(filename)
        filedata = readfile(filename)
        data = parse_ics(filedata, filename)
        if data == None:
            print("{} is not an ics file, skipping".format(filename))
            continue
        jsdata = json.dumps(data)
        jsfile = filename+'.json'
        if writefile(jsfile, jsdata):
            if verbose > -1:
                print("{} -> {} converted".format(filename,jsfile))
        else:
            print("Error writing {}".format(jsfile))
    return 0


if __name__ == '__main__':
    # taskdir = os.path.abspath(os.getcwd())
    # taskdir = os.getcwd()
    taskdir = '.'

    if sys.argv[1] == '-v':
        verbose = 1
        taskdir = sys.argv[2]
    elif sys.argv[1] == '-vv':
        verbose = 2
        taskdir = sys.argv[2]
    else:
        taskdir = sys.argv[1]
    if verbose:
        print("You are running `{}`".format(" ".join(sys.argv)))
    rc = main(taskdir)
    sys.exit(rc)

