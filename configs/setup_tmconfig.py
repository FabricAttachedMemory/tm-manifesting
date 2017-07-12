#!/usr/bin/python3
"""
Running on ToRMS, scan the complex and create an INI template for consumption
by the Librarian's "book_register.py -j".  Automatic determination of values
depends on adherence to the host naming standard, DNS, and FAM and SoC power
state (On :-) of all desired nodes.  Hints are given on stderr, the INI file
comes to stdout.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


import requests as HTTP_REQUESTS
import sys
import time
from types import SimpleNamespace as GenericObject

from pdb import set_trace

import dns.resolver as RES

_MAX_ENCLOSURES = 4
_MAX_NODES_PER_ENCLOSURE = 10

###########################################################################
# Templates for pieces of the INI file

_global_template = '''# TMConfig INI file {timestamp}
# {ReviewHint}  When you are satisfied, run
# "book_register.py -j <filename>" to create the final tmconfig file.

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

_node_template = '''[{hostname}]
node_id = {node_id}
nvm_size = {nbooks}B
'''

###########################################################################


def get(URL):
    '''A wrapper around requests.get, it expects JSON from Redfish.'''

    timeout = 0.2
    while timeout < 1.0:    # three tries
        try:
            resp = HTTP_REQUESTS.get(URL, timeout=timeout)
            assert resp.status_code == 200, \
                'Bad response code %d' % resp.status_code
            return resp.json()
        except HTTP_REQUESTS.exceptions.ConnectTimeout as e:
            timeout *= 2
        except Exception as e:
            break
    return None

###########################################################################


def redfishURI(IPaddrstr, subURI=''):
    '''From an IP address and optional suffix, create a Redfish query URL.'''
    tmp =  'http://%s:8081/redfish/v1/MgmtService' % IPaddrstr
    if subURI:
        tmp += subURI
    return tmp

###########################################################################


def trace(msg, EOL=True):
    '''Typing convenience wrapper for output to stderr.'''
    print(msg, end='\n' if EOL else '', file=sys.stderr)

###########################################################################


def getHeader():
    '''Fill an object with global values gleaned from DNS.'''
    hdr = GenericObject(
        needsReview=False,     # Or did all fields get calculated?
        timestamp='auto-generated on %s' % (time.ctime())
    )
    try:
        res = RES.query('torms', 'A')   # If this is a real ToRMS, this works
        FQDN = str(res.qname)
        assert FQDN.endswith('.mft.labs.hpecorp.net.'), 'Bad suffix'
        elems = FQDN[:-1].split('.')
        assert len(elems) == 6, 'Bad length'
        assert elems[0] == 'torms', 'Not torms'
        DC, rack = elems[1].split('-')   # XYZp-abcde
        assert len(DC) == 4 and DC[-1] == 'p', 'Bad DC'
        hdr.Datacenter = DC[:3].upper()
        hdr.Rack = rack
        hdr.Domain = '.'.join(elems[1:])
    except Exception as e:
        hdr.needsReview = True
        hdr.Datacenter = 'OnTheMoon'
        hdr.Rack = 'FtC99'
        hdr.Domain = 'have.it.your.way'
    return hdr

###########################################################################


def getEnclosures(hdr):
    '''Scan the MP space for Zswitch MPs (just the first one).'''
    hdr.enclosures = []
    for enc in range(1, _MAX_ENCLOSURES + 1):
        trace('Probing for enclosure %d ' % enc, False)
        alive = get(redfishURI('10.254.%d.101' % enc))     # Just the first SMP
        trace('BINGO!' if alive else '')
        if alive:
            hdr.enclosures.append(enc)

###########################################################################


def getNodeFAM(hdr):
    '''Scan the known enclosures for powered nodes, then probe MCs for FAM.'''
    hdr.node_count = 0
    hdr.enc2nodeFAM = {}
    for enc in hdr.enclosures:
        trace('')
        hdr.enc2nodeFAM[enc] = []
        for node in range(1, _MAX_NODES_PER_ENCLOSURE + 1):
            hostname = 'node%02d' % (((enc - 1) * 10) + node)
            IPaddr = '10.254.%d.%d' % (enc, 200 + node)
            trace('Probing for enc %d node %2d (%s) ' % (enc, node, hostname),
                  False)
            URL = redfishURI(IPaddr, subURI='/Fabric')
            alive = get(URL)
            if alive and alive['PowerState'] == 'On':
                hdr.node_count += 1
                nbooks = 0
                for mc in range(1, 5):
                    mcdata = get(
                        redfishURI(
                            IPaddr, subURI='/FAM/MediaControllers/%d' % mc))
                    if mcdata is None or mcdata['MemoryState'] != 'On':
                        hdr.needsReview = True
                        nbooks = 4  # Minimum legal size for an INI file
                        break
                    nbooks += (mcdata['DimmCount'] * mcdata['DimmSize']) // 8
                trace('BINGO! FAM = %d books' % nbooks)
                hdr.enc2nodeFAM[enc].append(( node, nbooks ))
            else:
                trace('')

###########################################################################


def emitINI(hdr):
    '''Dump everything to stdout.'''
    print(_global_template.format(**vars(hdr)))

    # U-values for the "/Enclosure/Ux" substring of the full coordinate
    for enc in hdr.enclosures:
        print(_enclosure_template % (enc, ((enc - 1) * 10) + 1))

    # Nodes
    for enc in hdr.enclosures:
        for node, nbooks in hdr.enc2nodeFAM[enc]:     # It's a tuple
            node_id = ((enc -1 ) * 10) + node
            outdata = GenericObject(
                hostname='node%02d' % node_id,
                node_id=node_id,
                nbooks=nbooks)
            print(_node_template.format(**vars(outdata)))

###########################################################################


def main(cmdlineArgsNotUsed):
    '''Called by top-level setup.py. Gather data and emit an INI file.'''
    hdr = getHeader()

    getEnclosures(hdr)
    if not hdr.enclosures:
        trace('\nNo enclosures found.')
        return False

    getNodeFAM(hdr)
    if not hdr.node_count:
        trace('\nNo nodes found.')
        return False

    if hdr.needsReview:
        hdr.ReviewHint = 'NOT ALL VALUES COULD BE DETERMINED!'
    else:
        hdr.ReviewHint = 'All values were resolved properly.'

    trace('\nThe INI output starts now, redirect stdout to a file.\n')
    emitINI(hdr)
    trace('After redirecting stdout to a file ("tmconfig.ini"), edit it.')
    trace('Follow the directions in the comments at the top of the file.')
    trace(hdr.ReviewHint + '\n')
    return not hdr.needsReview


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
