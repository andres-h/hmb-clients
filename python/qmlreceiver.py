#!/usr/bin/env python3

import sys
import zlib
import tempfile
import datetime
import gnupg
from optparse import OptionParser
from hmb.client import HMB

VERSION = "0.2 (2020.042)"

RETRY_WAIT = 10

def handleEvent(data, gpg):
    print("{dateTime} M={magnitude} {location} -> {eventID}.xml".format(**data))

    with tempfile.NamedTemporaryFile() as f:
        f.write(data['signature'])
        f.flush()
        verified = gpg.verify_data(f.name, data['zquakeml'])

    if verified.trust_level is None or verified.trust_level < verified.TRUST_FULLY:
        print("signature not trusted, ignoring message", end="\n\n")
        return

    print("signed at",
        datetime.datetime.utcfromtimestamp(int(verified.sig_timestamp)), "UTC",
        "by", verified.username, end="\n\n")

    with open(data['eventID'] + '.xml', 'wb') as f:
        f.write(zlib.decompress(data['zquakeml']))

def worker(source, gpg):
    while True:
        for obj in source.recv():
            try:
                if obj['type'] == 'QUAKEML_EVENT':
                    handleEvent(obj['data'], gpg)

                elif obj['type'] == 'EOF':
                    print("Waiting for next events in real time")

            except (KeyError, TypeError) as e:
                print("invalid data received: " + str(e))

def main():
    parser = OptionParser(usage="usage: %prog [options]", version="%prog v" + VERSION)
    parser.set_defaults(timeout = 120, backfill = 10)

    parser.add_option("-H", "--source", type="string", dest="source",
        help="Source HMB URL")

    parser.add_option("-u", "--user", type="string", dest="user",
        help="Source HMB username")

    parser.add_option("-p", "--password", type="string", dest="password",
        help="Source HMB password")

    parser.add_option("-t", "--timeout", type="int", dest="timeout",
        help="Timeout in seconds (default %default)")

    parser.add_option("-b", "--backfill", type="int", dest="backfill",
        help="Number of messages to backfill (default %default)")

    parser.add_option("-g", "--gnupghome", type="string", dest="gnupghome",
        help="GnuPG home directory (default $HOME/.gnupg)")

    (opt, args) = parser.parse_args()

    if args:
        parser.error("incorrect number of arguments")

    if opt.source is None:
        parser.error("missing source HMB")

    param = {
        'heartbeat': opt.timeout//2,
        'queue': {
            'QUAKEML_EVENT': {
                'seq': -opt.backfill-1
            }
        }
    }

    auth = (opt.user, opt.password) if opt.user and opt.password else None

    source = HMB(opt.source, param, retry_wait=RETRY_WAIT,
            timeout=opt.timeout, auth=auth)

    gpg = gnupg.GPG(gnupghome=opt.gnupghome)

    print("Retrieving past {} events".format(opt.backfill))

    worker(source, gpg)

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        pass

