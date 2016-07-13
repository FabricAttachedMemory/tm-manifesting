# Config file for Manifest API, can be used from Python or Bash
# Noone, but maintainer, must modify this file. If you want different config file,
# then create your own following variable convention used in this file and pass
# it to your manifest_api.py with --config option.

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
L4TM_AREAS = ( 'contrib', 'non-free' )

TFTP_ROOT = MANIFESTING_ROOT + 'tftp/'
