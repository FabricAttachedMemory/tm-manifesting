"""
!!! NOTE: This script must only be used for manifest_api.py. Other use CASES
    are NOT tested and not acounted for !!!

    This module parses a python (.py) config file into local variables and
    constructs several other parameters that are useful for the manifesting
    api server.

    There are several pre-constructed tuple field in the beginning of this
    module that are used for validation of the config file. The other use
    case for this tuples is to organize and group setting parameters, such as
    "serve settings" (port, host, mirror...),
    "manifest environment" (root, manifest uploads...) and
    "tftp environment (root, images, grub...).
    This approach also allows the use of this module in slightly more
    automated fashion (example: setup script would use "manifest env" set to
    create all necessary directories used in it)
"""

from collections import namedtuple
import flask
import os
import sys

from pdb import set_trace

_mroot_field = 'MANIFESTING_ROOT'
_tftp_root_field = 'TFTP_ROOT'

_server_fields = (
                  'TMCONFIG',
                  'HOST',
                  'PORT',
                  'L4TM_MIRROR',
                  'L4TM_RELEASE',
                  'L4TM_AREAS'
                  )

_manifest_env = (
                'FILESYSTEM_IMAGES',
                'MANIFEST_UPLOADS',
                'GOLDEN_IMAGE'
               )

_tftp_env = (
            'TFTP_IMAGES',
            'TFTP_GRUB'
           )

_expected_fields = _server_fields + (_mroot_field, _tftp_root_field)

settings = {}

def make_config(config_path):
    """
        Unpack parameters of the passed config file into the local variables of
    this module.

    :param 'config_path': path to a .py config file.
    """
    global settings
    config_path = os.path.realpath(config_path)

    settings = _extract_from_config(config_path)

    # no trailing slashes
    mroot = os.path.join(settings['MANIFESTING_ROOT'])
    if mroot[-1] == '/':
        mroot = mroot[:-1]
    tftp = os.path.join(settings['TFTP_ROOT'])
    if tftp[-1] == '/':
        tftp = tftp[:-1]

    settings['MANIFESTING_ROOT'] = mroot
    settings['TFTP_ROOT'] = tftp
    settings['FILESYSTEM_IMAGES'] = mroot + '/sys-images'
    settings['MANIFEST_UPLOADS'] = mroot + '/manifests'
    settings['GOLDEN_IMAGE'] = settings['FILESYSTEM_IMAGES'] + '/golden/golden.arm.tar'

    settings['TFTP_IMAGES'] = tftp + '/nodes'
    settings['TFTP_GRUB'] = tftp + '/boot/grub'
    return settings


def ratify_config(manconfig, dontcare=None):
    '''Insure all paths specified in the config file exist.'''
    if dontcare is None or not dontcare:
        dontcare = ()
    missing = []

    for attr in (_mroot_field, _tftp_root_field) + _manifest_env + _tftp_env:
        if attr in dontcare:
            continue
        path = manconfig.get(attr, None)
        if path is None:
            missing.append('Missing path key "%s"' % attr)
        else:
            if not os.path.isdir(path) and not os.path.isfile(path):
                missing.append('Missing "%s" path "%s"' % (attr, path))

    return missing if missing else False


def _extract_from_config(config_path):
    """
        Validate that incoming .py config file has required variables set and
    return a dictionary of expected parameters.

    :param 'config_path': path to the .py config file.
    :return: [dict] pair of field names (variables) that will be used with its values.
    """
    flask_obj = flask.Flask('dummy_flask_obj')   # Just to pars .py config into dict
    flask_obj.config.from_pyfile(config_path)
    result = {}
    for expected in _expected_fields:
        if expected not in flask_obj.config:
            raise ValueError('Config file missing field  "%s"' % expected)
        result[expected] = flask_obj.config[expected]
    flask_obj = None        # Only needed it for from_object()
    return result
