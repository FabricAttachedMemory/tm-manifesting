#/usr/bin/python3 -tt
import os

tmconfig_path = os.path.realpath(__file__)
tmconfig_path = os.path.dirname(tmconfig_path)
TMCONFIG = '%s/hpetmconfig.json' % tmconfig_path

MANIFESTING_SERVER = 'http://zachv.americas.hpqcorp.net:31178/manifesting/api/'
TFTP = '/var/lib/tm-manifest/tftp/'
IMAGES = TFTP + 'images/'
