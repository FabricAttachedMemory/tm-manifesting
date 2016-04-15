DEBUG = True
PORT = 31178
HOST = '0.0.0.0'
MANIFESTING_SERVER_DIR = '/opt/hpetm/manifesting/'
SYSTEM_IMAGES_DIR = '/opt/hpetm/manifesting/sys-images/'

L4TM_MIRROR = 'http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm'
L4TM_RELEASE = 'catapult'
# Remove 'main' for a much faster starter (3 seconds vs 20)
L4TM_AREAS = ( 'contrib', 'non-free')
# L4TM_AREAS = ( 'main', 'contrib', 'non-free')
