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
import errno
import os
import sys

from pdb import set_trace

from tmms.utils import utils
from tmms.utils import core_utils
from tmms.utils import file_utils
from tmms.utils import customize_node
from tmms.utils import logging
from configs.build_config import ManifestingConfiguration


def customize_golden(manconfig, golden_tar, build_dir, logger=None):
    '''Combine /etc/tmms settings and some hardcoded values.'''
    #FIXME: make it a config file
    arg_values = {
        'is_golden' : True, # Modifies a lot of behavior in customize_node
        'hostname' : 'golden',
        'node_coord' : 'golden_custom',
        'node_id' : None,
        'tftp_dir' : build_dir,
        'repo_mirror' : manconfig['DEBIAN_MIRROR'],
        'repo_release' : manconfig['DEBIAN_RELEASE'],
        'repo_areas' : manconfig['DEBIAN_AREAS'],
        'other_mirrors' : manconfig['OTHER_MIRRORS'],
        'packages' : 'linux-image-4.14.0-l4fame-72708-ge6511d981425,l4fame-node',
        'golden_tar' : golden_tar,
        'build_dir' : build_dir,
        'status_file' : build_dir + '/status.json',
        'verbose' : False if logger is None else logger.verbose,
        'debug' : True,         # prevent fork/exec
        'logger' : logger
    }

    response = customize_node.execute(argparse.Namespace(**arg_values))

    if response['status'] >= 400:
        msg = '\n !!! -- Customization stage ended with ERROR(s) -- !!!\n%s' %\
                response['message']
        if logger is not None:
            logger.error(msg)
        raise RuntimeError(msg)

    golden_dir = os.path.dirname(golden_tar)
    core_utils.make_tar(build_dir + '/golden.arm.tar', build_dir + '/untar')
    file_utils.remove_target(build_dir + '/untar')

    if os.path.exists(golden_dir + '.raw'):
        file_utils.remove_target(golden_dir +'.raw')

    if logger is not None:
        logger.info(' -- Customization stage is finished. -- ')

    move_dir(golden_dir, golden_dir + '.raw', verbose=True)
    move_dir(build_dir, golden_dir, verbose=True)


def move_dir(target, into, verbose=False):
    move_status = file_utils.move_target(target, into, verbose)
    if move_status is False:
        raise RuntimeError(' - Failed to move %s into %s!' % (target, into))


def debootstrap_image(manconfig, vmd_path=None, logger=None):
    """
    @param manconfig: parsed tmms config file of type <ManifestingConfiguration>.
    @param vmd_path: (default=None) absolute path to a vmdconfig file. If not
                    starts with '/' or is None a default path will be used:
                    ("/[...]/tm-manifesting/config/filesystem/")
    """
    whereami = os.path.dirname(os.path.realpath(__file__))
    vmdebootstrap = 'vmdebootstrap'
    sampleVMDs = whereami + '/filesystem/'

    vmdconfig = vmd_path
    if not vmdconfig.startswith('/'):
        vmdconfig = sampleVMDs + vmdconfig

    if not os.path.isfile(vmdconfig):
        msg = 'Cannot find %s! Must be a filename or an absolute path!' % (vmdconfig)
        raise RuntimeError(msg)

    destfile = manconfig['GOLDEN_IMAGE']    # now I can have a KeyError
    #get directory of the golden image dest file to save build artifacts to
    destdir = os.path.realpath(os.path.dirname(destfile))
    statvfs = os.statvfs(destdir)

    if (statvfs.f_bsize * statvfs.f_bavail) < (10 * (1 << 30)):
        raise RuntimeError('Need at least 10G on "%s"' % (destdir))

    vmdlog = destdir + '/vmdebootstrap.log'
    vmdimage = destdir + '/golden.arm.img'

    cmd = '''{vmdebootstrap} --no-default-configs
             --config={vmd_cfg}
             --log={vmd_log}
             --tarball={tarball}
             --mirror={mirror}
             --distribution={distro}
          '''

    cmd = cmd.format(vmdebootstrap=vmdebootstrap,
                vmd_cfg=vmdconfig,
                vmd_log=vmdlog,
                tarball=destfile,
                mirror=manconfig['DEBIAN_MIRROR'],
                distro=manconfig['DEBIAN_RELEASE'])

    os.chdir(destdir)           # location of embedded debootstrap log file
    os.unsetenv('LS_COLORS')    # this value is big, pointless and distracting
    file_utils.remove_target(destdir + '/debootstrap.log')
    file_utils.remove_target(vmdlog)
    ret, _, _ = core_utils.piper(cmd, use_call=True)     # Watch it all go by

    # Get the directory which was the chroot populating the loopback mount.
    # Match a stanza in the deboostrap command line.
    pat = '%s /tmp/' % manconfig['DEBIAN_RELEASE']
    contents = open(vmdlog).readlines()
    tmp = [ t for t in contents if pat in t ]
    if len(tmp):
        tmp = '/tmp/' + tmp[-1].split('/tmp/')[1].split()[0]
        utils.kill_chroot_daemons(tmp)

    core_utils.create_loopback_files()     # LXC containers don't have them on restart.

    if not ret:
        return True

    errors = [ e for e in contents if 'WARN' in e or 'ERROR' in e ]

    if logger is not None: #sanity
        logger.error(''.join(errors), file=sys.stderr)  # already have newlines

    raise RuntimeError('vmdebootstrap failed, consult %s' % vmdlog)


def download_image(img_path, destination, logger=None):
    """
        Download golden image from local storage (if path is supplied) or from
    remote (if img_path is URL).
    """
    if isinstance(img_path, list):
        img_path = img_path[0]

    if logger is not None:
        logger.info(' - Getting golden image from %s' % (img_path))
    file_utils.from_url_or_local(img_path, destination)


def main(args):
    """
        Generate golden image into the manifesting work directory using
    vmdebootstrap.  Return None or raise error.
    """
    assert os.geteuid() == 0, 'This script requires root permissions'
    supplied_image = getattr(args, 'sysimage', None)

    manconfig = ManifestingConfiguration(args.config, autoratify=False)
    missing = manconfig.ratify(dontcare=('TMCONFIG', ))

    golden_tar = manconfig['GOLDEN_IMAGE']
    golden_dir = os.path.dirname(golden_tar)
    golden_custom = golden_dir + '_custom'

    logger = logging.tmmsLogger('golden', golden_custom + '/build.log', args.verbose)

    # -- Maybe build 'raw' golden image using vmdebootstrap --
    if supplied_image is None:
        if logger is not None:
            logger.info(' --- Starting Debootstrap Image stage --- ')
            logger.info('Note: to skip debootstrap, use --image <local path or url>')

        vmd_path = getattr(args, 'vmd_cfg', None)
        debootstrap_image(manconfig, vmd_path=vmd_path, logger=logger)
    else:
        if logger is not None:
            logger.info(' - Skipping bootstrap stage...')
        download_image(supplied_image, golden_tar, logger=logger)

    customize_golden(manconfig, golden_tar, golden_custom, logger=logger)


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
