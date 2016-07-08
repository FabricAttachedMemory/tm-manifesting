"""
    This module parses a .py config file into local variables and construct
several other parameters that are useful for the manifesting api server.

    There are several pre-constructed tuple field in the beginning of this module
that are used for validation of the config file. The other use case for this
tuples is to organize and group setting parameters, such as "serve settings" (port,
host, mirror...), "manifest environment" (root, manifest uploads...) and "tftp
environment (root, images, grub...). This approach also allows the use of this
module in slightly mor aotomated fashion (example: setup script would use "manifest
env" set to create all necesery directories used in it)
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

manifest_env = (
                'FILESYSTEM_IMAGES',
                'MANIFEST_UPLOADS',
                'GOLDEN_IMAGE'
               )

tftp_env = (
            'TFTP_IMAGES',
            'TFTP_GRUB'
           )

_expected_fields = _server_fields + (_mroot_field, _tftp_root_field)


def update(config_path):
    """
        Unpack parameters of the passed config file into the local variables of
    this module.

    :param 'config_path': path to a .py config file.
    """
    config_path = os.path.realpath(config_path)

    result = {}
    result = _extract_from_config(config_path)

    mroot = os.path.join(result['MANIFESTING_ROOT'], '')  # ensure trailing slashes
    tftp = os.path.join(result['TFTP_ROOT'], '')

    result['MANIFESTING_ROOT'] = mroot
    result['TFTP_ROOT'] = tftp
    result['FILESYSTEM_IMAGES'] = mroot + 'sys-images/'
    result['MANIFEST_UPLOADS'] = mroot + 'manifests/'
    result['GOLDEN_IMAGE'] = result['FILESYSTEM_IMAGES'] + 'golden/golden.arm.tar'

    result['TFTP_IMAGES'] = tftp + 'nodes/'
    result['TFTP_GRUB'] = tftp + 'boot/grub/'
    sys.modules[__name__].__dict__.update(result)
    return result


def _extract_from_config(config_path):
    """
        Validate that incoming .py config file has required variables set and
    return a dictionary of expected parameters.

    :param 'config_path': path to the .py config file.
    :return: [dict] pair of field names (variables) that will be used with its values.
    """
    flask_obj = flask.Flask(__name__)   # To pars .py config into dict
    flask_obj.config.from_pyfile(config_path)
    result = {}
    for expected in _expected_fields:
        if expected not in flask_obj.config:
            raise ValueError('Config file missing field  "%s"' % expected)
        result[expected] = flask_obj.config[expected]
    return result


_default_cfg = os.path.dirname(__file__) + '/default.py'
locals().update(update(_default_cfg))
