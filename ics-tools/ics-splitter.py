#!/usr/bin/env python3

"""
Small application to fix(?) ics files
"""

import pytz
import os
import sys
import re
import getopt
from uuid import uuid4
from copy import deepcopy

# --------------- magic here --------------- #

class MyICS():
    """Structured representation of ics data sets"""
 
    global_uidset = dict()

    def __init__(self, data: str =None,  file='',  verbose: int =0,  debug: dict =None):
        """Update internal class default values if needed."""
        self._verbose = verbose
        self._debug = debug
        if data != None:
            self.data = self.parse(data,  file)
        else:
            self.readfile(file)
 
    def _readfile(self, file) -> str:
        """Read from file return contents or empty string."""
        if file:
            try:
                if os.stat(file):
                    with open(file, 'r', encoding='utf8') as file_handle:
                        file_content = file_handle.read()
                    return file_content
            except FileNotFoundError as err:
                if self._verbose > 1:
                    print(err)
        return ''

    def _writefile(self, file: str, data: dict =None) -> bool:
        """Write data to file, use empty string if no data provided."""
        if file:
            if data is None:
                data = self.data
            try:
                with open(file, 'w', encoding='utf8') as file_handle:
                    file_handle.write(data)
            except OSError as err:
                if self._verbose > 1:
                    print(err)
                return False
        return True

    def get(self):
        return self.data

    def set(self, data: dict =None) -> bool:
        self.data = data
        return True
        
    def readfile(self, file) -> bool:
        if file != '':
            self.data = self.parse(self._readfile(file), file)
        return self.data != None

    def writefile(self, file) -> bool:
        if self.data == None:
            return False
        if file != '':
            data = self.write()
            if data == None:
                return False
            #print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            #print(data)
            #print("x--------------------------x")
            return self._writefile(file, data)
        return False

    def fixup(self):
        fixed = self.fix()
        if fixed == None:
            return False
        return self.set(fixed)

    def parse(self,  icsdata: str,  source='') -> dict:
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
                if self._verbose:
                    print("Not ics data")
                return None
            if self._debug:
                for pattern in self._debug:
                    if line.count(pattern):
                        print("Source '{}' Line {}: debug option found: {}".format(source, lineno, pattern))
                        print(' '+line)
                        print(" Context: "+' -> '.join(ctxstack))
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
                if self._verbose > 2:
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
                tokens = line.split(':')
                key = tokens[0]
                val = ':'.join(tokens[1:])
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

    def write(self, icsdata: dict =None) -> str:
        """Write structured ics dataset to string."""
        ctxnames_1 = { 'VEVENT': 1, 'VTODO': 1, 'VTIMEZONE': 1, 'ALARM': 1 }
        ctxnames_2 = { 'VALARM': 1, 'STANDARD': 1, 'DAYLIGHT': 1 }
        multivalue = [ 'ATTACH', 'ATTENDEE' ]
        if icsdata == None:
            icsdata = self.data
        ics = list()
        if 'VCALENDAR' not in icsdata:
            if self._verbose:
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
        
    def split(self,  data: dict = None) -> dict:
        """Split large ics vcalendar data into single VEVENT chunks."""

        if data == None:
            data = self.data
        if data == None:
            return None
        if ('VCALENDAR' not in data) or (data['VCALENDAR'] == None):
            return None
        if ('VEVENT' not in data['VCALENDAR']) or (data['VCALENDAR']['VEVENT'] == None):
            return None

        vgroups = [ 'VEVENT',  'VTODO' ]
        splitdata = dict()
        vcaldata = dict({'VCALENDAR': {}} )
        for key in data['VCALENDAR']:
            if key not in vgroups:
                vcaldata['VCALENDAR'][key] = data['VCALENDAR'][key]
        for vgroup in vgroups:
            if vgroup not in data['VCALENDAR']:
                continue
            for vgroup_iter in range(len(data['VCALENDAR'][vgroup])):
                vgroup_item = data['VCALENDAR'][vgroup][vgroup_iter]
                if 'UID' in vgroup_item:
                    uid = vgroup_item['UID']
                else:
                    uid = str(uuid4())
                splitdata[uid] = deepcopy(vcaldata)
                splitdata[uid]['VCALENDAR'][vgroup] = [ vgroup_item ]
        if len(splitdata.keys()) == 1:
            # Nothing to split, just one entry!
            return None
        return splitdata


# --------------- end of magic --------------- #


# --------- mains --------- #

def usage():
    pass

def getfiles(topdir) -> list:
    filelist = list()
    for root, dirs, files in os.walk(topdir, topdown=False):
        for name in files:
            filelist.append(os.path.join(root, name))
    return filelist

def cmpfiles(a=None, b=None, verbose: bool =False) -> bool:
    if (a == None) or (b == None):
        return False
    res = True
    lineno = 0
    with open(a) as f1, open(b) as f2:
        for line1, line2 in zip(f1, f2):
            lineno += 1
            if line1 != line2:
                if verbose:
                    print(f"files differ on line {lineno}:\n{line1}{line2}")
                return False
    return res


def main() -> int:
    """Main loop to run thru all files in the given directory."""
     # taskdir = os.path.abspath(os.getcwd())
    # taskdir = os.getcwd()
    taskdir = '.'
    verbose = 0
    debug = list()
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvd:", ["help", "debug="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        return 2
    for o, a in opts:
        if o == "-v":
            verbose += 1
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--debug"):
            debug.append(a)
        else:
            assert False, "unhandled option"
            return 7
    if verbose:
        print("You are running `{}`".format(" ".join(sys.argv)))
    if len(args) > 0:
        taskdir = args[0]
    if len(args) > 1:
        print("extra arguments detected: {}".format(args[1:]))    
 
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
            print("reading {}".format(filename))
        cal = MyICS(file=filename, verbose=verbose, debug=debug)
        if None == cal.get():
            print("skipping {}: not an ics file".format(filename))
            continue
        
        splits = cal.split()
        if splits == None:
            if verbose:
                print("skipping {}: single entry".format(filename))
            continue
        # print(splits)
        # break

        for k in splits.keys():
            cal.set(splits[k])
            if cal.writefile(k):
                if k == filename:
                    print("overwriting {}".format(filename))
                print("{} written".format(k))
            else:
                print("error writing {}".format(k))
    return 0


if __name__ == '__main__':
    sys.exit(main())

