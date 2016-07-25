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

    # An "environment" is a collection of keys for values that may be
    # directory paths, file names, or just data.  _configfile_env must
    # be found in the Flask configuration file.  The other _envs build
    # on that and are hardcoded in this module.  FIXME: type tags.

    _configfile_env = (
        'MANIFESTING_ROOT',
        'TFTP_ROOT',
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
        'TFTP_GRUB',
        'DNSMASQ_CONFIGS'
    )

    _all_env = _configfile_env + _manifest_env + _tftp_env

    _settings = {}

    def __init__(self, flask_config_path, autoratify=True):
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
            'DNSMASQ_CONFIGS':      mroot + '/dnsmasq',

            'TFTP_ROOT':            tftp,
            'TFTP_IMAGES':          tftp + '/images',
            'TFTP_GRUB':            tftp + '/boot/grub',
        })

        if autoratify:
            errors = self.ratify()
            if errors:
                raise ValueError('\n'.join(errors))

    # Duck-type a read-only dict.  It's empty before extract_flask_config()
    def __getitem__(self, key):
        return self._settings.get(key, None)

    def keys(self):
        return sorted(self._settings.keys())

    @property
    def manifesting_keys(self):
        return frozenset(self._manifest_env)

    @property
    def tftp_keys(self):
        return frozenset(self._tftp_env)

    def ratify(self, dontcare=None):
        '''Insure all keys and their associated data exist.'''
        if not dontcare:
            dontcare = ()
        missing = []
        for key in frozenset(self._all_env) - frozenset(dontcare):
            path = self[key]
            if path is None:
                missing.append('Missing key "%s"' % key)
                continue
            # FIXME: tagged keys would be better
            try:
                if not path.startswith('/'):
                    continue                # String but not a path
            except AttributeError as e:     # Not a string
                continue

            if not (os.path.isdir(path) or
                    os.path.isfile(path) or
                    os.path.islink(path)):
                missing.append('Missing "%s" path "%s"' % (key, path))
        return missing

    def _extract_flask_config(self):
        """
        Use Flask convenience routine to parse the main config file.
        """

        flask_obj = flask.Flask(time.ctime())   # dummy name
        flask_obj.config.from_pyfile(self._flask_config_path)
        self._settings = {}
        for key in self._configfile_env:
            if key not in flask_obj.config:
                raise ValueError('Config file missing "%s"' % key)
            self._settings[key] = flask_obj.config[key]
        flask_obj = None
