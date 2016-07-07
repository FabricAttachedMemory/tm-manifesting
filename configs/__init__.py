import flask
import os
from pdb import set_trace

#from . import config

_flask_app = flask.Flask(__name__)
_expected_fields = ('TMCONFIG', 'HOST', 'PORT',
                    'L4TM_MIRROR', 'L4TM_RELEASE', 'L4TM_AREAS',
                    'MANIFESTING_ROOT', 'TFTP_ROOT')

'''
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
        locals()[field] = _flask_app.config[field]
        #result[field] = _flask_app.config[field]
   # set_trace()
    #locals().update(result)
'''

def validate_config(config_dict):
    """
        Validate that incoming .py config file has required variables set.
    """
    for expected in _expected_fields:
        if expected not in config_dict:
            raise ValueError('Config file missing field  "%s"' % expected)


def get_expected():
    """
        Extract required config variables from .py config file.
    """
    result = {}
    for field in _expected_fields:
        result[field] = _flask_app.config[field]
    return result


_default_cfg = os.path.dirname(__file__) + '/default.py'
_flask_app.config.from_pyfile(_default_cfg)
validate_config(_flask_app.config)

locals().update(get_expected())
