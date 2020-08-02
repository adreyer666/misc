#!/usr/bin/env python3

"""
Small library to parse ics data sources
"""

# --------------- magic here --------------- #


def parse_ics(icsdata: str, source='', verbose=False) -> dict:
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

# --------------- end of magic --------------- #


if __name__ == '__main__':
    print("This file contains an ics parsing library. No need to call it directly.")

