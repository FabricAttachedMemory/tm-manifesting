#!/usr/bin/python3 -tt

import argparse
import errno
import json
import os
import os.path
import shlex
import shutil
import subprocess
import sys

from pdb import set_trace

# Imports are relative because implicit Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration

from utils.utils import make_dir, make_symlink


def main(args):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Setup arguments intended for tmms developers only')
    parser.add_argument(
        '-P', '--packaging',
        help='This flag should only be set by post-setup scripts in Debian ' +
             'installer. Using it while trying to run from the git repo ' +
             'will result in a non-functioning environment.\n',
        action='store_true')

    # A fresh L4TM may not have some things, including flask.
    # Chicken-and-egg: flask is needed to parse config file

    args, _ = parser.parse_known_args()
    try:
        main(args)
        raise SystemExit(0)
    except (AssertionError, RuntimeError, ValueError) as err:
        errmsg = str(err)
    except Exception as err:
        errmsg = 'UNEXPECTED ERROR: %s' % str(err)

    raise SystemExit('%s\nsetup failed' % errmsg)
