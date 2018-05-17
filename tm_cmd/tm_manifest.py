#!/usr/bin/python3
"""
 This is a "tm-manifest" command line tool that lets users interuct with tm-manifesting-server
api. Check man page for available commands or run tm-manifest -h.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


import argparse
from pdb import set_trace
import sys

from tmcmd import cmdlookup


def main(args):
    if len(args['leftover']) == 0:
        cmdlookup['help']()
        return

    # at this point, sys.argv should only have arguments known to 'cmdlookup'
    # e.g: sys.argv = ['tm_manifest.py', '--port', '56666', 'list'] is now ['list']
    try:
        endpoint_type = args['leftover'][0]
        endpoint_args = args['leftover'][1:]
        print(cmdlookup[endpoint_type](endpoint_args, **args))
    except KeyError as e:
        print('Unknown argument %s!' % (e))
    except Exception as e:              # Show me the stack trace NOT!
        if args['debug']:
            set_trace()
            pass
        raise SystemExit(str(e))        # shell callers need non-zero exit


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='Optional arguments for API.')

    PARSER.add_argument('--port', default='31178',
                        help='Port for the server to be used. ' +\
                             'NOTE: os env TM_MANIFEST_SERVERPORT is prioritized ' +\
                             'over this arg.')
    PARSER.add_argument('--server', default='localhost',
                        help='Server base for the manifesting to be used.' +\
                             'NOTE: os env TM_MANIFEST_SERVERPORT is prioritized ' +\
                             'over this arg.')

    PARSER.add_argument('--verbose', '-v',
                        help='Make it talk.',
                        action='store_true')
    PARSER.add_argument('--debug',
                        help='Turn on debugging tool.',
                        action='store_true')
    ARGS, leftover = PARSER.parse_known_args()
    ARGS.leftover = leftover
    main(vars(ARGS))

    raise SystemExit(0)
