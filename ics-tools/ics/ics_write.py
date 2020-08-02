#!/usr/bin/env python3

"""
Small library to parse ics data sources
"""

# --------------- magic here --------------- #


def write_ics(icsdata: dict, verbose=False) -> str:
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

# --------------- end of magic --------------- #


if __name__ == '__main__':
    print("This file contains an ics writing function. No need to call it directly.")

