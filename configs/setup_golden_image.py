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

from configs.build_config import ManifestingConfiguration
#from utils.file_utils import remove_target
from tmms.utils import customize_node
from tmms.utils import file_utils
from tmms.utils import utils as tmms_utils


GOLDEN_DIR='/var/lib/tmms/sys-images/golden/'

def customize_golden(golden_tar, build_dir):
    arg_values = {
        'hostname' : 'golden',
        'node_coord' : 'golden_custom',
        'node_id' : None,
        'tftp_dir' : build_dir,
        'repo_mirror' : 'http://seedy.us.rdlabs.hpecorp.net',
        'repo_release' : 'jessie',
        'repo_areas' : ('main', 'contrib', 'non-free'),
        'other_mirrors' : 'deb http://hlinux-deejay.us.rdlabs.hpecorp.net/l4fame/ catapult main contrib non-free',
        'packages' : 'l4tm-archive-keyring, linux-image-arm64-l4tm, tm-zbridge, tm-flush, fam-atomic-driver, tm-fuse-4.7.2,tm-libfuse, tm-librarian',
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

    golden_dir = os.path.dirname(golden_tar)
    tmms_utils.compress(build_dir + '/untar', build_dir + '/golden.arm.tar')
    file_utils.remove_target(build_dir + '/untar')

    if os.path.exists(golden_dir + '.raw'):
        file_utils.remove_target(golden_dir +'.raw')

    move_dir(golden_dir, golden_dir + '.raw', verbose=True)
    move_dir(build_dir, golden_dir, verbose=True)

    print(' -- Customization stage is finished. -- ')


def move_dir(target, into, verbose=False):
    move_status = file_utils.move_target(target, into, verbose)
    if move_status is False:
        raise RuntimeError(' - Failed to move %s into %s!' %\
                            (target, into))


def debootstrap_image(tmms_cfg_path, vmd_path=None):
    """
    @param tmms_cfg_path: path to a tmms config file. Typically /etc/tmms or
                        /.../tm-manifesting/tmms.
    @param vmd_path: (default=None) absolute path to a vmdconfig file. If not
                    starts with '/' or is None a default path will be used:
                    ("/[...]/tm-manifesting/config/filesystem/")
    """
    whereami = os.path.dirname(os.path.realpath(__file__))
    vmdebootstrap = whereami + '/vmdebootstrap'
    sampleVMDs = whereami + '/filesystem/'

    if vmd_path is None:
        vmdconfig = sampleVMDs + 'golden.arm.duo.vmd'
    else:
        vmdconfig = vmd_path
        if not vmdconfig.startswith('/'):
            vmdconfig = sampleVMDs + vmdconfig

    assert os.path.isfile(vmdconfig), 'Cannot find ' + vmdconfig

    manconfig = ManifestingConfiguration(tmms_cfg_path, autoratify=False)
    missing = manconfig.ratify(dontcare=('GOLDEN_IMAGE', 'TMCONFIG'))

    destfile = manconfig['GOLDEN_IMAGE']    # now I can have a KeyError
    if not os.path.exists(destfile):
        print(' - Destination does not exist. Creating %s' % destfile)
        file_utils.make_dir(destfile)

    destdir = os.path.realpath(os.path.dirname(destfile))
    statvfs = os.statvfs(destdir)
    assert statvfs.f_bsize * statvfs.f_bavail > (10 * (1 << 30)), \
        'Need at least 10G on "%s"' % (destdir)

    vmdlog = destdir + '/vmdebootstrap.log'
    vmdimage = destdir + '/golden.arm.img'

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
        destfile,
        manconfig['L4TM_MIRROR'],
        manconfig['L4TM_RELEASE'])

    os.chdir(destdir)           # location of embedded debootstrap log file
    os.unsetenv('LS_COLORS')    # this value is big, pointless and distracting
    file_utils.remove_target(destdir + '/debootstrap.log')
    file_utils.remove_target(vmdlog)
    ret, _, _ = tmms_utils.piper(cmd, use_call=True)     # Watch it all go by

    # Get the directory which was the chroot populating the loopback mount.
    # Match a stanza in the deboostrap command line.
    pat = '%s /tmp/' % manconfig['L4TM_RELEASE']
    contents = open(vmdlog).readlines()
    tmp = [ t for t in contents if pat in t ]
    if len(tmp):
        tmp = '/tmp/' + tmp[-1].split('/tmp/')[1].split()[0]
        tmms_utils.kill_chroot_daemons(tmp)

    tmms_utils.create_loopback_files()     # LXC containers don't have them on restart.

    if not ret:
        return True

    errors = [ e for e in contents if 'WARN' in e or 'ERROR' in e ]
    print(''.join(errors), file=sys.stderr)    # They already have newlines
    raise RuntimeError('vmdebootstrap failed, consult %s' % vmdlog)


def download_image(img_path):
    """
        Download golden image from local storage (if path is supplied) or from
    remote (if URL is passed).
    """
    if isinstance(img_path, list):
        img_path = img_path[0]

    if os.path.exists(img_path):
        if not os.path.isfile(img_path):
            raise RuntimeError(' - E - %s is not a golden image file!')

        #TODO: check if path is a tar file.
        print(' - Local path to golden will be used to get image from:\n -- %s ' %\
            (img_path))
        img_basename = os.path.basename(img_path)

        file_utils.copy_target_into(img_path, GOLDEN_DIR + img_basename)
        return
    else:
        print(' - %s is not a local path. Goint to check url...' % img_path)

    raise RuntimeError(' - E - Downloading golden image from URL is not yet implemented!')


def main(args):
    """
        Generate golden image into the manifesting work directory using
        vmdebootstrap.  Return None or raise error.
    """
    assert os.geteuid() == 0, 'This script requires root permissions'

    # -- Build 'raw' golden image using vmdebootstrap --
    if not getattr(args, 'skip_bootstrap', False):
        return
        vmd_path = args.extra[1] if len(args.extra) >= 2 else None
        debootstrap_image(args.config, vmd_path=vmd_path)
    else:
        print (' -- Skipping bootstrap stage, since --skip-bootstrap param used.')

    if getattr(args, 'golden', False) is not False:
        download_image(args.golden)

    # -- Customizing Golden Image stage --
    golden_dir = '/var/lib/tmms/sys-images/golden'
    golden_custom = golden_dir + '_custom'
    customize_golden(golden_dir + '/golden.arm.tar', golden_custom)



if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
