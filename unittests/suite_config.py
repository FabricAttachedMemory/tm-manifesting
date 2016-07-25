#!/usr/bin/python3 -tt
import requests
import os
import sys

from tm_librarian.tmconfig import TMConfig
from pdb import set_trace

from tmms.configs import build_config
config_file = os.path.dirname(__file__) + '/config.unittests'

# ------------------------------

import tmms.tm_cmd.tmcmd as TMCMD

# ------------------------------

server_config = build_config.ManifestingConfiguration(config_file)
tmcmd = TMCMD
hpetmconfig = TMConfig(server_config['TMCONFIG'])
if hpetmconfig.errors:
    raise SystemExit('Bad TMCF:\n' + '\n'.join(hpetmconfig.errors))

MANIFESTING_SERVER = 'http://localhost:31178/manifesting/api/'


def isServerRunning(server):
    try:
        http_resp = requests.get(server)
    except requests.exceptions.RequestException:
        return False
    return True
