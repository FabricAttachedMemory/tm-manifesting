#!/usr/bin/python3 -tt
import os
import flask

#from . import default

from pdb import set_trace

app = flask.Flask(__name__)
app.config.from_pyfile(os.path.realpath('./default.py'))

set_trace()

_mroot = default.MANIFESTING_ROOT
_tftp = default.TFTP_ROOT

MANIFESTING_ROOT = _mroot
FILESYSTEM_IMAGES = os.path.normpath(_mroot + '/sys-images/')
MANIFEST_UPLOADS = os.path.normpath(_mroot + '/manifests/')
GOLDEN_IMAGE = os.path.normpath(FILESYSTEM_IMAGES + '/golden/golden.arm.tar')

TFTP_IMAGES = os.path.normpath(_tftp + '/nodes/')
TFTP_GRUB = os.path.normpath(_tftp + 'boot/grub/')
