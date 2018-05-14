#!/usr/bin/python3 -tt
"""
!!! NOTE: This script must only be used for manifesting commands.
    Other use cases are NOT tested or supported !!!

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
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


from collections import namedtuple
import inspect
import os
import sys
import time

from pdb import set_trace


class ManifestingConfiguration(object):

    # An "environment" is a collection of keys for values that may be
    # directory paths, file names, or just data.  _configfile_env must
    # be found in the Flask configuration file.  The other _envs build
    # on that and are hardcoded in this module.

    # TMDOMAIN removed from "required" fields as it's deprecated in
    # favor of "domains{}" in TMCF.  More to follow.

    _configfile_env = (
        'MANIFESTING_ROOT',
        'TFTP_ROOT',
        'TMCONFIG',
        'HOST',
        'PORT',
        'DEBIAN_MIRROR',
        'DEBIAN_RELEASE',
        'DEBIAN_AREAS',
        'OTHER_MIRRORS',
        'PXE_INTERFACE',
        'PXE_FIREWALL'
    )

    _manifest_env = (           # New directories are keyed from here
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
            'GOLDEN_IMAGE':         fsimages + '/golden/golden.tar',
            'MANIFEST_UPLOADS':     mroot + '/manifests',
            'DNSMASQ_CONFIGS':      mroot + '/dnsmasq',

            'TFTP_ROOT':            tftp,
            'TFTP_IMAGES':          tftp + '/images',
            'TFTP_GRUB':            tftp + '/grub',     # grub EFI "prefix"
        })

        # Final updates based on previous contents.  PID file is needed by
        # manifest_api, log file is referenced at startup but not "needed".
        # setup_networing should follow lead of using PREFPATH for file names.
        self._settings['DNSMASQ_PREPATH'] = '%s/%s' % (
            self._settings['DNSMASQ_CONFIGS'], self._settings['PXE_INTERFACE'])
        self._settings['DNSMASQ_PIDFILE'] = '%s.pid' % (
            self._settings['DNSMASQ_PREPATH'])
        self._settings['DNSMASQ_LOGFILE'] = '%s.log' % (
            self._settings['DNSMASQ_PREPATH'])

        # Convert all "None" strings to an actual None python type.
        for key, val in self._settings.items():
            if isinstance(val, str) and val.lower() == 'none':
                self._settings[key] = None

        if autoratify:
            errors = self.ratify()
            if errors:
                raise ValueError('\n'.join(errors))


    def get(self, key, default_value):
        ''' Same functionality as of dict.get(). Return a key if in the settings,
        or default_value instead. '''
        return self._settings.get(key, default_value)


    # Duck-type a dict.  It's empty before extract_flask_config().  The
    # flask routines turn the string value 'None' into Python None.
    def __getitem__(self, key):
        return self._settings.get(key)

    def __setitem__(self, key, value):
        self._settings[key] = value

    def __contains__(self, key):
        return key in self._settings

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
            try:
                path = self[key]    # Note that None is a valid value
            except KeyError:
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
                missing.append('Missing "%s" target "%s"' % (key, path))
        return missing

    def _extract_flask_config(self):
        """
        Use Flask convenience routine to parse the main config file.
        Note this converts a string value of 'None' into Python's None.
        """
        import flask    # DE102: this must come AFTER installing base packages

        try:
            flask_obj = flask.Flask(time.ctime())   # dummy name
            flask_obj.config.from_pyfile(self._flask_config_path)
        except NameError as e:
            raise RuntimeError('%s; should it be a string?' % str(e))
        self._settings = {}
        missing = []
        # Parse required tmms config values
        for key in self._configfile_env:
            if key in flask_obj.config:
                self._settings[key] = flask_obj.config[key]
                flask_obj.config.pop(key) # remove key, since already parsed
            else:
                missing.append(key)

        # Get all the other values in the tmms config
        for cfg_key, cfg_value in flask_obj.config.items():
            if cfg_key not in self._settings:   # should always be true
                self._settings[cfg_key] = cfg_value
            else:
                print(' - W - Getting tmms key that already being parsed? %s : %s' %\
                        (cfg_key, cfg_value))

        if missing:
            raise ValueError('Config file missing "%s"' % ', '.join(missing))

        # New variable(s) not ready for auto/forced inclusion.

        for key in ('PXE_SUBNET', ):
            self._settings[key] = flask_obj.config.get(key, 'None')

        flask_obj = None

    @staticmethod
    def tmms_chroot(ref=1):
        '''Relocate the apparent file path to account for symlinks.'''
        # http://stackoverflow.com/questions/11757801/get-the-file-of-the-function-one-level-up-in-the-stack
        # It lives here because this is a known import from the repo
        # top-level commands setup_*.py and manifest_api.py.
        actual = inspect.getfile(sys._getframe(ref))
        actual = os.path.realpath(actual)
        actual = os.path.dirname(actual)
        return actual


if __name__ == '__main__':
    from ..setup import jfdi
