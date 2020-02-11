#!/usr/bin/env python3

import sys
from optparse import OptionParser
from hmb.client import HMB

VERSION = "0.1 (2020.042)"

RETRY_WAIT = 10

def handlePick(data):
    print(data)

def worker(source):
    while True:
        for obj in source.recv():
            try:
                if obj['type'] == 'PICK':
                    handlePick(obj['data'])

                elif obj['type'] == 'EOF':
                    print("Waiting for further picks within the same region and time in real time")

            except (KeyError, TypeError) as e:
                print("invalid data received: " + str(e))

def main():
    parser = OptionParser(usage="usage: %prog [options] latmin latmax lonmin lonmax starttime endtime", version="%prog v" + VERSION)
    parser.set_defaults(timeout = 120)

    parser.add_option("-H", "--source", type="string", dest="source",
        help="Source HMB URL")

    parser.add_option("-u", "--user", type="string", dest="user",
        help="Source HMB username")

    parser.add_option("-p", "--password", type="string", dest="password",
        help="Source HMB password")

    parser.add_option("-t", "--timeout", type="int", dest="timeout",
        help="Timeout in seconds (default %default)")

    (opt, args) = parser.parse_args()

    if len(args) != 6:
        parser.error("incorrect number of arguments")

    latmin = float(args[0])
    latmax = float(args[1])
    lonmin = float(args[2])
    lonmax = float(args[3])
    starttime = args[4]
    endtime = args[5]

    if opt.source is None:
        parser.error("missing source HMB")

    param = {
        'heartbeat': opt.timeout//2,
        'queue': {
            'PICK': {
                'seq': 0,
                'starttime': starttime,
                'endtime': endtime,
                'filter': {
                    '$and': [
                        {'data.latitude': {'$gte': latmin, '$lte': latmax}},
                        {'data.longitude': {'$gte': lonmin, '$lte': lonmax}}
                    ]
                }
            }
        }
    }

    auth = (opt.user, opt.password) if opt.user and opt.password else None

    source = HMB(opt.source, param, retry_wait=RETRY_WAIT,
            timeout=opt.timeout, auth=auth)

    worker(source)

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        pass

