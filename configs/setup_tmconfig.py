#!/usr/bin/python3
"""
    Scan the complex and create an INI template for consumption by
the Librarian's "book_register.py -j".
"""

import argparse
import os
import requests as HTTP_REQUESTS
import sys
import time
from types import SimpleNamespace as GenericObject

import dns.resolver as RES
from netaddr import IPNetwork, iter_iprange, IPAddress
import netifaces as NIF

from pdb import set_trace

# Imports are relative to parent directory with setup.py because implicit
# Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration
from utils.utils import basepath, piper, setDhcpClientId
from utils.file_utils import make_symlink, make_dir

MAX_ENCLOSURES = 4
MAX_NODES_PER_ENCLOSURE = 10

###########################################################################
# Templates for pieces of the INI file

_global_template = '''# TMConfig INI file {timestamp}
# You can change Datacenter, Rack, and Domain in the [global] section.
# Or leave them alone if you like.

[global]
Datacenter = {Datacenter}
Rack = {Rack}
Domain = {Domain}

node_count = {node_count}
book_size_bytes = 8G
'''

_enclosure_template = '''[enclosure%d]
U = U%d
'''

def get(URL):
    try:
        resp = HTTP_REQUESTS.get(URL, timeout=0.1)
        assert resp.status_code == 200, \
                'Bad response code %d' % resp.status_code
    except Exception as e:
        return None
    return resp.json()


def makeURL(IPaddrstr, subURI=''):
    tmp =  'http://%s:8081/redfish/v1/MgmtService' % IPaddrstr
    if subURI:
        tmp += subURI
    return tmp

def trace(msg, EOL=True):
    print(msg, end='\n' if EOL else '', file=sys.stderr)


def main(args):
    """
        scan and emit
    """
    hdr = GenericObject()
    hdr.node_count = 0
    hdr.Datacenter = 'OnTheMoon'
    hdr.Rack = 'FtC99'
    hdr.Domain = 'have.it.your.way'
    hdr.timestamp = 'auto-generated on %s' % (time.ctime())

    # Enclosures
    enclosures = []
    for enc in range(1, MAX_ENCLOSURES + 1):
        trace('Scanning for enclosure %d ' % enc, False)
        alive = get(makeURL('10.254.%d.101' % enc))     # Just the first SMP
        trace('BINGO!' if alive else '')
        if alive:
            enclosures.append(enc)

    nodes = {}
    for enc in enclosures:
        trace('')
        nodes[enc] = []
        for node in range(1, MAX_NODES_PER_ENCLOSURE + 1):
            trace('Scanning for enclosure %d node %2d ' % (enc, node), False)
            alive = get(makeURL('10.254.%d.%d' % (enc, 200 + node)))
            trace('BINGO!' if alive else '')
            if alive:
                nodes[enc].append(node)
                hdr.node_count += 1

    trace('\nThe desired output starts now, redirect stdout to a file.\n')

    print(_global_template.format(**vars(hdr)))
    for enc in enclosures:
        print(_enclosure_template % (enc, enc))

    for enc in enclosures:
        for node in nodes[enc]:
            node_id = ((enc -1 ) * 10) + node
            print('\n[node%02d]\nnode_id = %d' % (node_id, node_id))
            print('nvm_size = %dB' % 128)


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
