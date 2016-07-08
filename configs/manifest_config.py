import flask
import os
import sys
from pdb import set_trace


_flask_app = flask.Flask(__name__)
_expected_fields = ('TMCONFIG', 'HOST', 'PORT',
                    'L4TM_MIRROR', 'L4TM_RELEASE', 'L4TM_AREAS',
                    'MANIFESTING_ROOT', 'TFTP_ROOT')

_constructed_fields = ('FILESYSTEM_IMAGES', 'MANIFEST_UPLOADS',
                    'GOLDEN_IMAGE', 'TFTP_IMAGES', 'TFTP_GRUB')


def update(config_path):
    """
        Unpack local variables using python config file pass passed to this function.
    :param 'config_path': path to a .py config file.
    """
    config_path = os.path.realpath(config_path)
    _flask_app.config.from_pyfile(config_path)

    validate_config(_flask_app.config)
    result = {}
    for field in _expected_fields:
        result[field] = _flask_app.config[field]

    result = get_expected(result)
    result['MANIFESTING_ROOT'] = os.path.join(result['MANIFESTING_ROOT'], '')  # ensure trailing slashes
    result['TFTP_ROOT'] = os.path.join(result['TFTP_ROOT'], '')

    mroot = result['MANIFESTING_ROOT']
    tftp = result['TFTP_ROOT']
    result['FILESYSTEM_IMAGES'] = mroot + 'sys-images/'
    result['MANIFEST_UPLOADS'] = mroot + 'manifests/'
    result['GOLDEN_IMAGE'] = result['FILESYSTEM_IMAGES'] + 'golden/golden.arm.tar'

    result['TFTP_IMAGES'] = tftp + 'nodes/'
    result['TFTP_GRUB'] = tftp + 'boot/grub/'

    sys.modules[__name__].__dict__.update(result)


def validate_config(config_dict):
    """
        Validate that incoming .py config file has required variables set.
    """
    for expected in _expected_fields:
        if expected not in config_dict:
            raise ValueError('Config file missing field  "%s"' % expected)


def get_expected(config):
    """
        Extract required config variables from .py config file.
    """
    result = {}
    for field in _expected_fields:
        if field in config:
            result[field] = config[field]
    return result


_default_cfg = os.path.dirname(__file__) + '/default.py'
_flask_app.config.from_pyfile(_default_cfg)
validate_config(_flask_app.config)

update(_default_cfg)
