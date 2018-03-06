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
import sys

from pdb import set_trace

from tmcmd import cmdlookup


def _cleanup_sysarg(sysargv, parsearg):
    """
        Remove "argparse" defined arguments from sys.argv list as well as any
    other ars that are not in cmdlookup.
    Mixing those two together causing confusion in the "cmdlookup"
    function calls.
    :param 'sysargv': [list] of arguments in "sys.argv"
    :param 'parsearg': [dict] of arguments set by "argparse" module.
    """
    to_remove = [] #arguments to be removed from sysargv
    for arg in sysargv:
        # remove all dashes and = signes from the argument
        arg_name = arg.strip('-').split('=')[0]
        if arg not in cmdlookup:
            # removing directly from sysargv will cause problems. Thus, save
            # what needs to be removed and do it after this loop is done.
            to_remove.append(arg)
            continue

        if arg_name in parsearg:
            sysargv.remove(arg)
            to_remove.append(arg)

    # at this point, it is safe to remove from sysargv list, since it is outside
    # the sysargv loop.
    for arg in to_remove:
        if arg in sysargv:
            sysargv.remove(arg)


def main(args):
    _cleanup_sysarg(sys.argv, args)
    if len(sys.argv) == 0:
        cmdlookup['help']()
        return

    # at this point, sys.argv should only have arguments known to 'cmdlookup'
    # e.g: sys.argv = ['tm_manifest.py', '--port', '56666', 'list'] is now ['list']
    try:
        print(cmdlookup[sys.argv[0]](sys.argv[1:], **args))
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
