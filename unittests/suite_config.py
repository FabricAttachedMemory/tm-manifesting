#!/usr/bin/python3 -tt
import os
import sys

from tm_librarian.tmconfig import TMConfig
from pdb import set_trace

# ------------------------------

configs = os.path.realpath(__file__)
configs = os.path.dirname(configs)
configs = '%s/../' % (configs)
sys.path.append(configs)

from configs import manifest_config

# ------------------------------

tmcmd_path = os.path.realpath(__file__).split('unittests')[0]
tmcmd_path = tmcmd_path + '/tm-manifest/tmcmd/'
sys.path.append(tmcmd_path)

import tmcmd as TMCMD

# ------------------------------

server_config = manifest_config
tmcmd = TMCMD
"""
tmconfig_path = os.path.realpath(__file__)
tmconfig_path = os.path.dirname(tmconfig_path)
tmconfig_path = '%s/hpetmconfig_test.json' % tmconfig_path
"""
hpetmconfig = TMConfig(manifest_config.TMCONFIG)

sys.path.remove(configs)
sys.path.remove(tmcmd_path)
