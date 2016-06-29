#/usr/bin/python3 -tt
import os
import sys
from pdb import set_trace

manifest_config = os.path.realpath(__file__)
manifest_config = os.path.dirname(manifest_config)
manifest_config = '%s/../../' % (manifest_config)
sys.path.append(manifest_config)

from configs import manifest_config

tmconfig_path = os.path.realpath(__file__)
tmconfig_path = os.path.dirname(tmconfig_path)
TMCONFIG = '%s/hpetmconfig.json' % tmconfig_path

MANIFESTING_SERVER = 'http://zachv.americas.hpqcorp.net:31178/manifesting/api/'
TFTP = manifest_config.TFTP_ROOT
IMAGES = TFTP + '/' + manifest_config.TFTP_IMAGES

set_trace()
sys.path.remove(manifest_config)
