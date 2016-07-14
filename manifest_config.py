# Config file for Manifest API, intended for use from the Manifesting
# scripts make_golden_image.py, make_grub_config.py, manifest_api.py.
# If you want a different config file, copy this file, modify it to your
# needs, and run any of the manifesting programs with "--config yourconfig"

# Global topology config file for an instance of The Machine
TMCONFIG='/etc/tmconfig'

# Top-level directories
MANIFESTING_ROOT = '/var/lib/tmms'

# manifest_api delivers DHCP and TFTP by configuring a copy of dnsmasq
TFTP_ROOT = MANIFESTING_ROOT + '/tftp'

# Select IP address in this system on which the Manifest API listens
HOST = '0.0.0.0'    # 0.0.0.0 means all of them
PORT = 31178        # listen on this port

# L4TM repo information
L4TM_MIRROR = 'http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm'
L4TM_RELEASE = 'catapult'

# Remove 'main' for a much faster start (3 seconds vs 20)
L4TM_AREAS = ( 'contrib', 'non-free' )

