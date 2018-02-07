#!/usr/bin/python3 -tt
"""
    Generate a golden image using vmdebootstrap script that was slightly
modified for the needs of manifesting. Modified vmdebootstrap is in
./configs/ folder.  Note: "normal" vmdebootstrap must also be installed
on the system to satisfy package dependencies.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


import argparse
from collections import namedtuple
import errno
import os
import sys

from pdb import set_trace

# Imports are relative to parent directory with setup.py because implicit
# Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration
from utils.file_utils import remove_target
from utils.utils import piper, create_loopback_files, kill_chroot_daemons
from tmms.utils import customize_node


def customize_golden(golden_tar, build_dir):
    arg_values = {
        'hostname' : 'golden',
        'node_coord' : 'golden_l4mdc',
        'node_id' : None,
        'tftp_dir' : build_dir,
        'repo_mirror' : 'http://seedy.us.rdlabs.hpecorp.net',
        'repo_release' : 'jessie',
        'repo_areas' : ('main', 'contrib', 'non-free'),
        'other_mirrors' : 'deb http://hlinux-deejay.us.rdlabs.hpecorp.net/l4fame/ catapult main contrib non-free',
        'packages' : 'l4tm-archive-keyring, linux-image-arm64-l4tm',
        'golden_tar' : golden_tar,
        'build_dir' : build_dir,
        'status_file' : build_dir + '/status.json',
        'verbose' : True,
        'debug' : True,
        'logger' : None
    }
    try:
        customize_node.execute(argparse.Namespace(**arg_values))
    except Exception as err:
        _, _, exc_tb = sys.exc_info()
        raise RuntimeError('%s:%s\n %s\n' %\
                            (os.path.basename(__file__), exc_tb.tb_lineno, err))



def main(args):
    """
        Generate golden image into the manifesting work directory using
        vmdebootstrap.  Return None or raise error.
    """
    assert os.geteuid() == 0, 'This script requires root permissions'

    customize_golden('/var/lib/tmms/sys-images/golden/golden.arm.tar',
                    '/var/lib/tmms/sys-images/golden_l4mdc/')
    return

    create_loopback_files()     # LXC containers don't have them on restart.

    whereami = os.path.dirname(os.path.realpath(__file__))
    vmdebootstrap = whereami + '/vmdebootstrap'
    sampleVMDs = whereami + '/filesystem/'
    try:
        vmdconfig = args.extra[1]
        if not vmdconfig.startswith('/'):
            vmdconfig = sampleVMDs + vmdconfig
    except IndexError:
        vmdconfig = sampleVMDs + 'golden.arm.duo.vmd'
    assert os.path.isfile(vmdconfig), 'Cannot find ' + vmdconfig

    manconfig = ManifestingConfiguration(args.config, autoratify=False)
    missing = manconfig.ratify(dontcare=('GOLDEN_IMAGE', 'TMCONFIG'))
    destfile = manconfig['GOLDEN_IMAGE']    # now I can have a KeyError
    destdir = os.path.realpath(os.path.dirname(destfile))
    statvfs = os.statvfs(destdir)
    assert statvfs.f_bsize * statvfs.f_bavail > (10 * (1 << 30)), \
        'Need at least 10G on "%s"' % (destdir)

    vmdlog = destdir + '/vmdebootstrap.log'
    vmdimage = destdir + '/golden.arm.img'
    #--image=%s

    cmd = '''%s --no-default-configs
             --config=%s
             --log=%s
             --tarball=%s
             --mirror=%s
             --distribution=%s
          ''' % (
        vmdebootstrap,
        vmdconfig,
        vmdlog,
    #    vmdimage,
        destfile,
        manconfig['L4TM_MIRROR'],
        manconfig['L4TM_RELEASE'])

    os.chdir(destdir)           # location of embedded debootstrap log file
    os.unsetenv('LS_COLORS')    # this value is big, pointless and distracting
    remove_target(destdir + '/debootstrap.log')
    remove_target(vmdlog)
    ret, _, _ = piper(cmd, use_call=True)     # Watch it all go by

    # Get the directory which was the chroot populating the loopback mount.
    # Match a stanza in the deboostrap command line.
    pat = '%s /tmp/' % manconfig['L4TM_RELEASE']
    contents = open(vmdlog).readlines()
    tmp = [ t for t in contents if pat in t ]
    if len(tmp):
        tmp = '/tmp/' + tmp[-1].split('/tmp/')[1].split()[0]
        kill_chroot_daemons(tmp)
    if not ret:
        return True
    errors = [ e for e in contents if 'WARN' in e or 'ERROR' in e ]
    print(''.join(errors), file=sys.stderr)    # They already have newlines
    raise RuntimeError('vmdebootstrap failed, consult %s' % vmdlog)


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
