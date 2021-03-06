#!/usr/bin/env python3

"""
Small application to fix ics files with "broken" UID or defective text
continuation.
"""

import os
import sys
import re
from uuid import uuid4

verbose = 0
mytag = 'FIXER'

# --------- main -------------------------------------------------------------

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
            with open(file, 'x', encoding='utf8') as file_handle:
                file_handle.write(data)
        except OSError as err:
            if verbose > 1:
                print(err)
            return False
    return True


def new_uuid() -> str:
    """Create new UUID as string."""
    uuid = str(uuid4())
    if verbose > 2:
        print("New UUID: ", uuid)
    return uuid


def main(taskdir) -> int:
    pattern = r'^\w+[\w-]+\w$'
    uidregex = re.compile(pattern)

    pattern = r'^\w+[\w\./@-]+\w$'
    extregex = re.compile(pattern)

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
        modified = False
        filedata = readfile(filename)
        lineno = 0
        newdata = list()
        for line in filedata.splitlines():
            lineno += 1
            # broken text continuation
            if line.startswith('\\'):
                if verbose:
                    print("Fixing line {} in {}".format(lineno, filename))
                newdata.append("  "+line)
                continue
            modify = False
            # Make UID a UUID if non-alphnumeric
            if line.startswith('UID:'):
                if line.rfind(':') > 3:
                    modify = True
                else:
                    (tag,uid) = line.split(':')
                    m = uidregex.match(uid)
                    if m == None:
                        modify = True
            if modify:
                # reset flag
                modify = False
                # replace and add extra line
                if verbose:
                    print("Fixing line {} in {}".format(lineno, filename))
                if verbose > 1:
                    print(line)
                newdata.append("X-"+mytag+"-"+line)
                newdata.append('UID:'+new_uuid())
                modified = True
                continue
            if line.startswith('X-RADICALE-NAME:'):
                # vdirsync chokes if 'X-RADICALE-NAME' is non-alphnumeric
                # RADICALE seems to sometimes have URLs or Timezone information
                # stored in it - here we just prepend another 'X' tag, so the tag
                # is no longer treated as an identifier
                if line.rfind(':') > 15:
                    modify = True
                else:
                    (tag,uid) = line.split(':')
                    m = extregex.match(uid)
                    if m == None:
                        modify = True
                    elif line.rfind('/') > -1:
                        line = 'X-TZID:'+uid 
            elif line.startswith('TZID:'):
                # vdirsync chokes if 'TZID' appears out of 'VTIMEZONE' context
                # luckily this seems only to happen with my local timezone
                if line.rfind(':') > 4:
                    modify = True
                elif line.startswith('TZID:Europe/London'):
                    modify = True
            if modify:
                # reset tag
                modify = False
                # rename tag
                if verbose:
                    print("Fixing line {} in {}".format(lineno, filename))
                if verbose > 1:
                    print(line)
                newdata.append("X-"+mytag+"-"+line)
                modified = True
                continue
            newdata.append(line)
        newdata.append('')
        if modified:
            if writefile(filename+'.new', "\n".join(newdata)):
                if verbose > -1:
                    print("{} modified".format(filename))
                os.rename(filename+'.new', filename)
            else:
                return 2
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

