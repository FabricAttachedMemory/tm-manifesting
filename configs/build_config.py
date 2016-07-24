"""
!!! NOTE: This script must only be used for manifest_api.py. Other use cases
    are NOT tested or supported !!!

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
import time

from pdb import set_trace


class ManifestingConfiguration(object):

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

    _required_fields = _server_fields + (_mroot_field, _tftp_root_field)

    _settings = {}

    def __init__(self, flask_config_path):
        """
        Unpack parameters of the passed config file into the local
        variables of this module.  It is assumed this file will then
        be used by manifest_api.py

        :param 'flask_config_path': path to a Flask config file.
        """
        self._flask_config_path = flask_config_path
        self._extract_flask_config()

        # no trailing slashes
        mroot = os.path.join(self['MANIFESTING_ROOT'])
        if mroot[-1] == '/':
            mroot = mroot[:-1]

        tftp = os.path.join(self['TFTP_ROOT'])
        if tftp[-1] == '/':
            tftp = tftp[:-1]

        fsimages = mroot + '/sys-images'

        # A few rewrites, a few new things
        self._settings.update({
            'MANIFESTING_ROOT':     mroot,
            'FILESYSTEM_IMAGES':    fsimages,
            'GOLDEN_IMAGE':         fsimages + '/golden/golden.arm.tar',
            'MANIFEST_UPLOADS':     mroot + '/manifests',

            'TFTP_ROOT':            tftp,
            'TFTP_IMAGES':          tftp + '/nodes',
            'TFTP_GRUB':            tftp + '/boot/grub'  # architected in grub
        })

    def __getitem__(self, key):     # Not valid before extract_flask_config()
        return self._settings.get(key, None)

    @property
    def manifesting_keys(self):
        return frozenset(self._manifest_env)

    @property
    def tftp_keys(self):
        return frozenset(self._tftp_env)

    def _ratify(self, dontcare=None):
        '''Insure all paths specified in the config file exist.'''
        if dontcare is None or not dontcare:
            dontcare = ()
        missing = []

        for attr in (_mroot_field, _tftp_root_field) + \
                _manifest_env + _tftp_env:
            if attr in dontcare:
                continue
            path = self[attr]
            if path is None:
                missing.append('Missing path key "%s"' % attr)
            else:
                if not os.path.isdir(path) and not os.path.isfile(path):
                    missing.append('Missing "%s" path "%s"' % (attr, path))

        return missing

    def _extract_flask_config(self):
        """
        Use Flask convenience routine to parse the main config file.
        """

        flask_obj = flask.Flask(time.ctime())   # dummy name
        flask_obj.config.from_pyfile(self._flask_config_path)
        self._settings = {}
        for f in self._required_fields:
            if f not in flask_obj.config:
                raise ValueError('Config file missing "%s"' % f)
            self._settings[f] = flask_obj.config[f]
        flask_obj = None
