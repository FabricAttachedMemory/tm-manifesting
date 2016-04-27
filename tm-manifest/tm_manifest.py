#!/usr/bin/python3 -tt
import argparse
from pdb import set_trace
import sys

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
        print(cmdlookup[sys.argv[1]](*tuple(sys.argv[2:]), **args))
    except (AssertionError, KeyError) as e:
        print(str(e))
        if args['debug']:
            set_trace()
            pass


if __name__ == '__main__':

    PARSER = argparse.ArgumentParser(description='Optional arguments for API.')

    PARSER.add_argument('--verbose',
                        help='Make it talk.',
                        action='store_true')
    PARSER.add_argument('--debug',
                        help='Turn on debugging tool.',
                        action='store_true')
    ARGS, _ = PARSER.parse_known_args()
    main(vars(ARGS))

    raise SystemExit(0)
