import os
import sys

API_VERSION = 1.0

DEBUG = True and sys.stdin.isatty()     #  running as a Deamon or from a Terminal?
VERBOSE = True and sys.stdin.isatty()   # enable debugging when from terminal...
PORT = 31178
HOST = '0.0.0.0'
MANIFESTING_ROOT = '/var/local/tm-manifesting'
FILESYSTEM_IMAGES = os.path.normpath(MANIFESTING_ROOT + '/sys-images')
MANIFEST_UPLOADS = os.path.normpath(MANIFESTING_ROOT + '/manifest_uploads')
GOLDEN_IMAGE = os.path.normpath(FILESYSTEM_IMAGES + '/golden/golden.l4tm.amd64.tar')

L4TM_MIRROR = 'http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm'
L4TM_RELEASE = 'catapult'
# Remove 'main' for a much faster starter (3 seconds vs 20)
L4TM_AREAS = ( 'contrib', 'non-free')
# L4TM_AREAS = ( 'main', 'contrib', 'non-free')

TMCONFIG = '/etc/tmconfig'
NODE_BINDING= '/etc/node_binding'
