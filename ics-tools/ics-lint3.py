#!/usr/bin/env python3

"""
Small application to fix(?) ics files
"""

import os
import sys
import re
# import json
import pytz
from uuid import uuid4
from ics import parse_ics, write_ics

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


def ics_fixup(data: dict) -> dict:
    # find "bad" uids 
    pattern = r'^\w+[\w-]+\w$'
    uidregex = re.compile(pattern)
    for event_iter in range(len(data['VCALENDAR']['VEVENT'])):
        vevent = data['VCALENDAR']['VEVENT'][event_iter]
        if 'UID' not in vevent:
            continue
        if uidregex.match(vevent['UID']) == None:
            data['VCALENDAR']['VEVENT'][event_iter]['UID'] = new_uuid()
    # check if TZID are official names
    for event_iter in range(len(data['VCALENDAR']['VEVENT'])):
        vevent = data['VCALENDAR']['VEVENT'][event_iter]
        if 'TZID' not in vevent:
            continue
        tz = data['VCALENDAR']['VEVENT'][event_iter]['TZID']
        if tz not in pytz.all_timezones:
            print("broken timezone id {}".format(tz))
    #
    return data
    return None





# --------- mains --------- #


def main(taskdir) -> int:

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
        data = parse_ics(filedata, filename, verbose)
        if data == None:
            print("{} is not an ics file, skipping".format(filename))
            continue
        
        fixdata = ics_fixup(data)
        if fixdata == None:
            print("fatal flaw in {}, skipping".format(filename))
            continue

        newdata = write_ics(data, verbose)
        newfile = filename+'.new'
        if writefile(newfile, newdata):
            if verbose > -1:
                print("{} -> {} modified".format(filename,newfile))
        else:
            print("Error writing {}".format(newfile))
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

