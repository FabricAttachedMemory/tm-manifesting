# Config file for Manifest API, can be used from Python or Bash

# Global topology config file for this instance of The Machine
TMCONFIG = '/etc/tmconfig'

# Select which interfaces on which the Manifest API listens
HOST = '0.0.0.0'    # bind to all interfaces in this computer
PORT = 31178        # listen on this port

# Working directory
MANIFESTING_ROOT = '/var/lib/tmms/'

# L4TM repo information
L4TM_MIRROR = 'http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm'
L4TM_RELEASE = 'catapult'

# Remove 'main' for a much faster starter (3 seconds vs 20)
#L4TM_AREAS = ( 'main' )
L4TM_AREAS = ( 'contrib', 'non-free' )
#L4TM_AREAS = ( 'main', 'contrib', 'non-free' )

TFTP_ROOT = MANIFESTING_ROOT + 'tftp/'
TFTP_IMAGES = 'nodes/'
TFTP_GRUB = 'boot/grub/'
