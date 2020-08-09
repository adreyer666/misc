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
import filecmp

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
        if self._verbose and (data == None):
            print("no data")
 
    def _readfile(self, file) -> str:
        """Read from file return contents or empty string."""
        if file:
            try:
                if os.stat(file):
                    # with open(file, 'r', encoding='utf8') as file_handle:
                    with open(file, 'rb') as file_handle:
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
            line = str(line, 'utf-8', 'ignore')
            if (lineno == 1) and (line.endswith('BEGIN:VCALENDAR')):
                if not line.startswith('BEGIN:VCALENDAR'):
                    # trim binary blob..
                    line = str("BEGIN:VCALENDAR")
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
        
    def fix(self,  data: dict = None) -> dict:
        """Fix up broken/non-compliant or non-interchangeable ics data provided in structured dataset."""

        if data == None:
            data = self.data
        if data == None:
            return None
        if ('VCALENDAR' not in data) or (data['VCALENDAR'] == None):
            return None
        if ('VEVENT' not in data['VCALENDAR']) or (data['VCALENDAR']['VEVENT'] == None):
            return None

        # - find "bad" uids
        # - vdirsyncer checks for unique uids
        # - vdirsyncer treats 'X-RADICALE-NAME' like a UID (?!)
        uidset = dict()
        vgroups_1 = [ 'VEVENT',  'VTODO' ]
        vgroups_2 = [ 'VALARM' ]
        vproperties = [ 'UID',  'X-RADICALE-NAME' ]
        propregex = dict()
        propregex['UID'] = re.compile(r'^\w[a-zA-Z0-9-]+\w$')          # underscore is not allowed, so \w does not work
        propregex['X-RADICALE-NAME'] = re.compile(r'^[\w\./_-]+$')
        for vgroup_1 in vgroups_1:
            if vgroup_1 not in data['VCALENDAR']:
                continue
            for vgroup_iter_1 in range(len(data['VCALENDAR'][vgroup_1])):
                vgroup_item_1 = data['VCALENDAR'][vgroup_1][vgroup_iter_1]
                for vprop in vproperties:
                    # check for duplicates in properties (1st level)
                    if vprop not in vgroup_item_1:
                        continue
                    p = vgroup_item_1[vprop]
                    if p.endswith('.ics'):
                        if self._verbose:
                            print("fixing property id with '.ics': {}".format(p))
                        data['VCALENDAR'][vgroup_1][vgroup_iter_1][vprop] = str(uuid4())
                    if (p in uidset) or (p in self.global_uidset):
                        if self._verbose:
                            print("fixing non-unique property id {}".format(p))
                        data['VCALENDAR'][vgroup_1][vgroup_iter_1][vprop] = str(uuid4())
                        if self._verbose > 1:
                            print("{} -1-- {}".format(p,data['VCALENDAR'][vgroup_1][vgroup_iter_1][vprop]))
                    uidset[data['VCALENDAR'][vgroup_1][vgroup_iter_1][vprop]] = 1
                for vgroup_2 in vgroups_2:
                    if vgroup_2 not in vgroup_item_1:
                        continue
                    for vgroup_iter_2 in range(len(vgroup_item_1[vgroup_2])):
                        # check for duplicates in nested properties (2nd level)
                        for vprop in vproperties:
                            if vprop not in vgroup_item_1[vgroup_2][vgroup_iter_2]:
                                continue
                            p = vgroup_item_1[vgroup_2][vgroup_iter_2][vprop]
                            if p.endswith('.ics'):
                                if self._verbose:
                                    print("fixing property id with '.ics': {}".format(p))
                                data['VCALENDAR'][vgroup_1][vgroup_iter_1][vgroup_2][vgroup_iter_2][vprop] = str(uuid4())
                            if (p in uidset) or (p in self.global_uidset):
                                if self._verbose:
                                    print("fixing non-unique property id {}".format(p))
                                data['VCALENDAR'][vgroup_1][vgroup_iter_1][vgroup_2][vgroup_iter_2][vprop] = str(uuid4())
                                if self._verbose > 1:
                                    print("{} -2- {}".format(p,data['VCALENDAR'][vgroup_1][vgroup_iter_1][vgroup_2][vgroup_iter_2][vprop]))
                            uidset[data['VCALENDAR'][vgroup_1][vgroup_iter_1][vgroup_2][vgroup_iter_2][vprop]] = 1
                # check propregex
                for vprop in vproperties:
                    if vprop not in vgroup_item_1:
                        continue
                    # print("vprop: {} - {}\npropregex: {}".format(vprop, vgroup_item_1[vprop],  propregex[vprop]))
                    if propregex[vprop].match(vgroup_item_1[vprop]) == None:    # property value not matching pattern
                        if self._verbose:
                            print("fixing poor/bad property id {}".format(vgroup_item_1[vprop]))
                        data['VCALENDAR'][vgroup_1][vgroup_iter_1][vprop] = str(uuid4())
                    uidset[data['VCALENDAR'][vgroup_1][vgroup_iter_1][vprop]] = 1
        self.global_uidset.update(uidset)
        # DT properties have TZ included no need to specify TZID (errors on radicale)
        for event_iter in range(len(data['VCALENDAR']['VEVENT'])):
            vevent = data['VCALENDAR']['VEVENT'][event_iter]
            if 'TZID' in vevent:
                del data['VCALENDAR']['VEVENT'][event_iter]['TZID']
        ## -- following part disabled (see above) -- ##
        ## # check if TZID are official names
        ## for event_iter in range(len(data['VCALENDAR']['VEVENT'])):
        ##     vevent = data['VCALENDAR']['VEVENT'][event_iter]
        ##     if 'TZID' not in vevent:
        ##         continue
        ##     tz = data['VCALENDAR']['VEVENT'][event_iter]['TZID']
        ##     if tz not in pytz.all_timezones:
        ##         print("broken timezone id {}".format(tz))
        ## --------- end of disabled part --------- ##
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
                if (k == 'X-RADICALE-NAME') and ('UID' in vevent) and (vevent['UID'] == vevent['X-RADICALE-NAME']):
                    ## TODO: check if this is correct...
                    ## they shouldn't be the same as the previous fix should have modified one of them!
                    #badkeys.append(k)
                    data['VCALENDAR']['VEVENT'][event_iter][k] = str(uuid4())
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
                        if self._verbose > 1:
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
                            if self._verbose > 1:
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
    taskfiles = list()
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvd:f:", ["help", "debug=", "file="])
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
        elif o in ("-f", "--file"):
            taskfiles.append(a)
        else:
            assert False, "unhandled option"
            return 7
    if verbose:
        print("You are running `{}`".format(" ".join(sys.argv)))
    if len(args) > 0:
        taskdir = args[0]
    if len(args) > 1:
        print("extra arguments detected: {}".format(args[1:]))    

    if len(taskfiles) == 0:
        try:
            os.stat(taskdir)
        except FileNotFoundError as err:
            if verbose:
                print('Directory not found, exiting.')
            if verbose > 1:
                print(err)
            return 1
        taskfiles = getfiles(taskdir)

    for filename in taskfiles:
        if filename.startswith('\.'):
            # skip dotfiles
            continue
        if verbose:
            print("reading {}".format(filename))
        cal = MyICS(file=filename, verbose=verbose, debug=debug)
        if None == cal.get():
            print("skipping {}: not an ics file".format(filename))
            continue
        
        if not cal.fixup():
            print("skipping {}: fatal flaw".format(filename))
            continue

        newfile = filename+'.new'
        if cal.writefile(newfile):
            if verbose > 1:
                print("{} written".format(filename, newfile))
            # compare old and new..
            unchanged = cmpfiles(filename, newfile, (verbose>0))
            if unchanged:
                os.remove(newfile)
            else:
                if verbose > -1:
                    print("{} -> {} modified".format(filename, newfile))
                pass
        else:
            print("error writing {}".format(newfile))
    return 0


if __name__ == '__main__':
    sys.exit(main())

