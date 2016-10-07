#!/usr/bin/python3

import argparse
import sys

from pdb import set_trace

from tmcmd import cmdlookup


def _cleanup_sysarg(sysargv, parsearg):
    """
        Remove "argparse" defined arguments from sys.argv list.
    Mixing those two together causing confusion in the "cmdlookup"
    function calls.
    :param 'sysargv': [list] of arguments in "sys.argv"
    :param 'parsearg': [dict] of arguments set by "argparse" module.
    """
    for arg in parsearg.keys():
        overlap = '--%s' % (arg)
        if overlap in sysargv:
            sysargv.remove(overlap)


def main(args):
    if len(sys.argv) < 2:
        cmdlookup['help']()
        return
    _cleanup_sysarg(sys.argv, args)
    try:
        print(cmdlookup[sys.argv[1]](sys.argv[2:], **args))
    except KeyError as e:
        raise SystemExit('No such directive %s' % str(e))
    except Exception as e:              # Show me the stack trace NOT!
        if args['debug']:
            set_trace()
            pass
        raise SystemExit(str(e))	# shell callers need non-zero exit


if __name__ == '__main__':

    PARSER = argparse.ArgumentParser(description='Optional arguments for API.')

    PARSER.add_argument('--verbose',
                        help='Make it talk.',
                        action='store_true')
    PARSER.add_argument('--debug',
                        help='Turn on debugging tool.',
                        action='store_true')
    ARGS, leftover = PARSER.parse_known_args()
    ARGS.leftover = leftover
    main(vars(ARGS))

    raise SystemExit(0)
