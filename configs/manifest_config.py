import os

API_VERSION = 1.0

DEBUG = True
PORT = 31178
HOST = '0.0.0.0'
MANIFESTING_SERVER_DIR = '/opt/hpetm/manifesting/'
SYS_IMGS = '/opt/hpetm/manifesting/sys-images/'		# Location of all the system images
MANIFESTS_DIR = '/opt/hpetm/manifesting/manifests/'
GOLDEN_IMG = os.path.normpath('%s/golden/golden.l4tm.amd64.tar' % (SYS_IMGS))

L4TM_MIRROR = 'http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm'
L4TM_RELEASE = 'catapult'
# Remove 'main' for a much faster starter (3 seconds vs 20)
L4TM_AREAS = ( 'contrib', 'non-free')
# L4TM_AREAS = ( 'main', 'contrib', 'non-free')

TMCONFIG_FILE = '/etc/hpetmconfig.json'
