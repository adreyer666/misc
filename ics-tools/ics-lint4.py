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


# --------------- magic here --------------- #


def parse_ics(icsdata: str, source='', verbose=False) -> dict:
    """Parse string into structured ics dataset."""
    ctxnames_1 = { 'VEVENT': 1, 'VTODO': 1, 'VTIMEZONE': 1, 'ALARM': 1 }
    ctxnames_2 = { 'VALARM': 1, 'STANDARD': 1, 'DAYLIGHT': 1 }
    multivalue = [ 'ATTACH', 'ATTENDEE' ]
    lineno = 0
    data = dict()
    ctxstack = list()
    key = None
    ctx_1 = None
    ctx_2 = None
    caldata = None
    for line in icsdata.splitlines():
        lineno += 1
        if (lineno == 1) and (not line.startswith('BEGIN:VCALENDAR')):
            if verbose:
                print("Not ics data")
            return None
        if line.startswith('BEGIN:'):
            (tag,ctx) = line.split(':')
            ctxstack.append(ctx)
            if ctx == 'VCALENDAR':
                caldata = dict()
                ctx_1 = None
                ctx_2 = None
            elif ctx in ctxnames_1:
                ctx_1 = dict()
                ctx_2 = None
            elif ctx in ctxnames_2:
                ctx_2 = dict()
            else:
                print("unknown context; source {} line {}".format(source,lineno))
                print(line)
                continue
        elif line.startswith('END:'):
            (tag,ctx) = line.split(':')
            if ctx != ctxstack[-1]:
                print("out of context; source {} line {}".format(source,lineno))
                print(line)
            if verbose:
                print("Context: "+' -> '.join(ctxstack))
            del ctxstack[-1]
            if ctx == 'VCALENDAR':
                data[ctx] = caldata
            elif (ctx == 'VEVENT') or (ctx == 'VTODO') or (ctx == 'VTIMEZONE') or (ctx == 'ALARM'):
               
                if ctx_1 == None:
                    print("context missing; source {} line {}".format(source,lineno))
                    print(line)
                    continue
                if ctx in caldata:
                    caldata[ctx].append(ctx_1)
                else:
                    caldata[ctx] = [ ctx_1, ]
                ctx_1 = None
            elif (ctx == 'VALARM') or (ctx == 'STANDARD') or (ctx == 'DAYLIGHT'):
                if (ctx_2 == None) or (ctx_1 == None):
                    print("context missing; source {} line {}".format(source,lineno))
                    print(line)
                    continue
                if ctx in ctx_1:
                    ctx_1[ctx].append(ctx_2)
                else:
                    ctx_1[ctx] = [ ctx_2, ]
                ctx_2 = None
            else:
                print("unknown context; source {} line {}".format(source,lineno))
                print(line)
                continue
        elif (line.startswith(' ')) or (line.startswith('\\')):
            if line.startswith('\\'):
                line = ' '+line     ## fix brokenness
            if not key:
                print("broken continuation; source {} line {}".format(source,lineno))
                print(line)
                print("Context: "+' -> '.join(ctxstack))
                continue
            if ctx_2 != None:
                if key in ctx_2:
                    ctx_2[key] += '\n'+line
                else:
                    ctx_2[key] = line
            elif ctx_1 != None:
                if key in ctx_1:
                    ctx_1[key] += '\n'+line
                else:
                    #print("broken continuation; source {} line {}".format(source,lineno))
                    #print(line)
                    #print("Context: "+' -> '.join(ctxstack))
                    #print("key: {}\nctx: {}".format(key,ctx_1))
                    ctx_1[key] = line
            else:
                if key in caldata:
                    caldata[key] += '\n'+line
                else:
                    caldata[key] = line
        else:
            if line.count(':') == 0:
                print("broken continuation?; source {} line {}".format(source,lineno))
                print(line)
                print("Context: "+' -> '.join(ctxstack))
                continue
            token = line.split(':')
            key = token[0]
            val = ':'.join(token[1:])
            if key in multivalue:
                if ctx_2 != None:
                    if key in ctx_2:
                        ctx_2[key].append(val)
                    else:
                        ctx_2[key] = [ val, ]
                elif ctx_1 != None:
                    if key in ctx_1:
                        ctx_1[key].append(val)
                    else:
                        ctx_1[key] = [ val, ]
                else:
                    if key in caldata:
                        caldata[key].append(val)
                    else:
                        caldata[key] = [ val, ]
            else:
                if ctx_2 != None:
                    ctx_2[key] = val
                elif ctx_1 != None:
                    ctx_1[key] = val
                else:
                    caldata[key] = val
    data['VCALENDAR'] = caldata
    return data


def write_ics(icsdata: dict, verbose=False) -> str:
    """Write structured ics dataset to string."""
    ctxnames_1 = { 'VEVENT': 1, 'VTODO': 1, 'VTIMEZONE': 1, 'ALARM': 1 }
    ctxnames_2 = { 'VALARM': 1, 'STANDARD': 1, 'DAYLIGHT': 1 }
    multivalue = [ 'ATTACH', 'ATTENDEE' ]
    ics = list()
    if 'VCALENDAR' not in icsdata:
        if verbose:
            print("Not ics data")
        return None
    ics.append("BEGIN:VCALENDAR")
    data = icsdata['VCALENDAR']
    keys_1 = data.keys()
    for key_1 in keys_1:
        if key_1 not in ctxnames_1:
            if key_1 in multivalue:
                 for k in data[key_1]:
                     ics.append("{}:{}".format(key_1,k))
            else:
                 ics.append("{}:{}".format(key_1,data[key_1]))
        else:
            for item_1 in data[key_1]:
                ics.append("BEGIN:{}".format(key_1))
                for key_2 in item_1.keys():
                    if key_2 not in ctxnames_2:
                        if key_2 in multivalue:
                            for k in item_1[key_2]:
                                ics.append("{}:{}".format(key_2,k))
                            pass
                        else:
                            ics.append("{}:{}".format(key_2,item_1[key_2]))
                    else:
                        for item_2 in item_1[key_2]:
                            ics.append("BEGIN:{}".format(key_2))
                            for key_3 in item_2.keys():
                                if key_3 in multivalue:
                                    for k in item_2[key_3]:
                                        ics.append("{}:{}".format(key_3,k))
                                else:
                                    ics.append("{}:{}".format(key_3,item_2[key_3]))
                            ics.append("END:{}".format(key_2))
                ics.append("END:{}".format(key_1))
    ics.append("END:VCALENDAR")
    return '\n'.join(ics)


global_uidset = dict()

def ics_fixup(data: dict) -> dict:
    """Fix up broken/non-compliant or non-interchangeable ics data provided in structured dataset"""
    if data == None:
        return None
    if ('VCALENDAR' not in data) or (data['VCALENDAR'] == None):
        return None
    if ('VEVENT' not in data['VCALENDAR']) or (data['VCALENDAR']['VEVENT'] == None):
        return None

    # - find "bad" uids
    # - vdirsyncer checks for unique uids
    uidset = dict()
    pattern = r'^\w+[\w-]+\w$'
    uidregex = re.compile(pattern)
    for event_iter in range(len(data['VCALENDAR']['VEVENT'])):
        vevent = data['VCALENDAR']['VEVENT'][event_iter]
        if 'UID' not in vevent:
            continue
        if (vevent['UID'] in uidset) or (vevent['UID'] in global_uidset):
            if verbose:
                print("fixing non-unique uid {}".format(vevent['UID']))
            data['VCALENDAR']['VEVENT'][event_iter]['UID'] = new_uuid()
        if uidregex.match(vevent['UID']) == None:
            if verbose:
                print("fixing bad uid {}".format(vevent['UID']))
            data['VCALENDAR']['VEVENT'][event_iter]['UID'] = new_uuid()
        uidset[data['VCALENDAR']['VEVENT'][event_iter]['UID']] = 1
    global_uidset.update(uidset)
    # check if TZID are official names
    for event_iter in range(len(data['VCALENDAR']['VEVENT'])):
        vevent = data['VCALENDAR']['VEVENT'][event_iter]
        if 'TZID' not in vevent:
            continue
        tz = data['VCALENDAR']['VEVENT'][event_iter]['TZID']
        if tz not in pytz.all_timezones:
            print("broken timezone id {}".format(tz))
    # Thunderbird Lightning chokes on composite 'TRIGGER'
    # entries with VALUE=DURATION (VCALENDAR > VEVENT > VALARM)
    # and composite 'DTSTAMP' properties with VALUE=DATE
    # (VCALENDAR > VEVENT )
    # it also adds annoying 'X-LIC-ERROR' entry
    for event_iter in range(len(data['VCALENDAR']['VEVENT'])):
        vevent = data['VCALENDAR']['VEVENT'][event_iter]
        badkeys = list()
        value = None
        for k in vevent.keys():
            if k.startswith('X-LIC-ERROR'):
                badkeys.append(k)
            if k.startswith('DTSTAMP;VALUE=DATE'):
                value = vevent[k]
                badkeys.append(k)
        for k in badkeys:
            del data['VCALENDAR']['VEVENT'][event_iter][k]
        if value != None:
            data['VCALENDAR']['VEVENT'][event_iter]['DTSTAMP'] = value
        if 'VALARM' not in vevent:
            continue
        for alarm_iter in range(len(data['VCALENDAR']['VEVENT'][event_iter]['VALARM'])):
            valarm = data['VCALENDAR']['VEVENT'][event_iter]['VALARM'][alarm_iter]
            badkeys = list()
            value = None
            for k in valarm.keys():
                if k.startswith('TRIGGER;VALUE=DURATION'):
                    if verbose:
                        print("fixing duration alarm trigger")
                    value = valarm[k]
                    badkeys.append(k)
                if k.startswith('X-LIC-ERROR'):
                    badkeys.append(k)
            for k in badkeys:
                del data['VCALENDAR']['VEVENT'][event_iter]['VALARM'][alarm_iter][k]
            if value != None:
                data['VCALENDAR']['VEVENT'][event_iter]['VALARM'][alarm_iter]['TRIGGER'] = value
    # Thunderbird Lightning chokes on composite 'TRIGGER'
    # entries with VALUE=DURATION (VCALENDAR > VTODO > VALARM)
    # it also adds annoying 'X-LIC-ERROR' entry
    if 'VTODO' in data['VCALENDAR']:
        for event_iter in range(len(data['VCALENDAR']['VTODO'])):
            vevent = data['VCALENDAR']['VTODO'][event_iter]
            if 'VALARM' not in vevent:
                continue
            for alarm_iter in range(len(data['VCALENDAR']['VTODO'][event_iter]['VALARM'])):
                valarm = data['VCALENDAR']['VTODO'][event_iter]['VALARM'][alarm_iter]
                badkeys = list()
                value = None
                for k in valarm.keys():
                    if k.startswith('TRIGGER;VALUE=DURATION'):
                        if verbose:
                            print("fixing duration alarm trigger")
                        value = valarm[k]
                        badkeys.append(k)
                    if k.startswith('X-LIC-ERROR'):
                        badkeys.append(k)
                for k in badkeys:
                    del data['VCALENDAR']['VTODO'][event_iter]['VALARM'][alarm_iter][k]
                if value != None:
                    data['VCALENDAR']['VTODO'][event_iter]['VALARM'][alarm_iter]['TRIGGER'] = value
    #
    return data

# --------------- end of magic --------------- #


# --------- mains --------- #


def main(taskdir) -> int:
    """Main loop to run thru all files in the given directory."""
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

