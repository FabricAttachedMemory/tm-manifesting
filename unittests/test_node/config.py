#/usr/bin/python3 -tt
import os
import sys
from pdb import set_trace

configs = os.path.realpath(__file__)
configs = os.path.dirname(configs)
configs = '%s/../../' % (configs)
sys.path.append(configs)

from configs import manifest_config

tmcmd_path = os.path.realpath(__file__).split('unittests')[0]
tmcmd_path = tmcmd_path + '/tm-manifest/tmcmd/'
sys.path.append(tmcmd_path)

import tmcmd

tmnode = tmcmd.tmnode
tmmanifest = tmcmd.tmmanifest

tmconfig_path = os.path.realpath(__file__)
tmconfig_path = os.path.dirname(tmconfig_path)
TMCONFIG = '%s/hpetmconfig.json' % tmconfig_path

MANIFESTING_SERVER = 'http://zachv.americas.hpqcorp.net:31178/manifesting/api/'
TFTP = manifest_config.TFTP_ROOT
IMAGES = TFTP + '/' + manifest_config.TFTP_IMAGES

sys.path.remove(configs)
sys.path.remove(tmcmd_path)
