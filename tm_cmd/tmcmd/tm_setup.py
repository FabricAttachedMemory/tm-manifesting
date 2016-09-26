#!/usr/bin/python3 -tt

import os
import shlex
import subprocess

from pdb import set_trace

from . import tm_base


class TmSetup(tm_base.TmCmd):

    def __init__(self):
        """
            Define 'args' for this class.
        """
        super().__init__()
        self.args = {
            'setup' : self.do_setup,
        }

    def do_setup(self, arg_list=None, **options):
        """
        setup

        Invoke the setup directives for manifesting.  You must be root.
        """
        assert not os.geteuid(), 'You must be root'
        dirname = os.path.dirname
        setup = dirname(dirname(dirname(globals()['__file__']))) + '/setup.py'
        assert os.path.isfile(setup), '"setup" directive only valid on ToRMS'

        # Just do an exec, but only from batteries included
       
        cmdlist = shlex.split('%s %s' % (setup, ' '.join(arg_list)))
        raise SystemExit(subprocess.call(cmdlist))