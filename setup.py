#!/usr/bin/python3 -tt

# Grab all possible arguments for all possible sub-scripts and do them (all).

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

from utils.setup_environment import add_cmdline_args as aca1, main as main1
from utils.setup_networking import add_cmdline_args as aca2, main as main2
from utils.setup_golden_image import add_cmdline_args as aca3, main as main3


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Setup arguments intended for tmms developers only')
    set_trace()
    aca1(parser)
    aca2(parser)
    aca3(parser)

    args, argvleft = parser.parse_known_args()
    try:
        main(args)
        raise SystemExit(0)
    except (AssertionError, RuntimeError, ValueError) as err:
        errmsg = str(err)
    except Exception as err:
        errmsg = 'UNEXPECTED ERROR: %s' % str(err)

    raise SystemExit('%s\nsetup failed' % errmsg)
