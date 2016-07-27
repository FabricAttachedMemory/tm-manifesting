#!/usr/bin/python3 -tt
'''System images'''

from collections import defaultdict
import gzip
import os
import glob
import fnmatch
import requests as HTTP_REQUESTS
import warnings
import sys

from debian.deb822 import Packages
from io import BytesIO, StringIO
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify, send_file

_ERS_element = 'sys-image'

# See the README in the main templates directory.
BP = Blueprint(_ERS_element, __name__)

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/%s/' % _ERS_element)
def webpage_show_all_tar(name=None):
    return render_template(
        _ERS_element + '_all.tpl',
        label=__doc__,
        keys=sorted(_data.keys()),
        url_base=request.url)


@BP.route('/%s/<name>' % _ERS_element)
def webpage_download_tar(name):
    file_location = _data.get(name, None)
    if file_location is None:
        return jsonify({ 'error': 'No such system image "%s"' % name })
    file_name = os.path.basename(file_location)
    return send_file(file_location,
                    as_attachment=True,
                    attachment_filename=file_name)

###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/api/%s/' % _ERS_element)
def api():
    return data_to_json()


@BP.route('/api/%s/<name>' % _ERS_element)
def api_download(name=None):
    """ This has exact the same logic as webpage_download_tar. """
    return webpage_download_tar(name)

###########################################################################


def data_to_json():
    result = defaultdict(list)
    for img_name in _data.keys():
        if 'golden' in img_name:
            result['golden'].append(img_name)
        else:
            result['custom'].append(img_name)
    return jsonify({'sys-image' : result })

###########################################################################

_data = None


def _load_data(mainapp):
    # https://github.com/raumkraut/python-debian/blob/master/README.deb822

    global _data
    _data = {}
    sys_img_dir = mainapp.config['FILESYSTEM_IMAGES']

    for abs_path, dirname, files in os.walk(sys_img_dir):
        for filename in fnmatch.filter(files, '*.tar'):
            _data[filename] = os.path.join(abs_path, filename)


def _filter(imgs):    # Maybe it's time for a class
    return [ sysimg for sysimg in imgs if sysimg not in _data ]

def register(mainapp):  # take what you like and leave the rest
    BP.UPLOADS = os.path.join(mainapp.root_path, 'blueprints/nodes/uploads/')
    BP.filter = _filter
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _load_data(mainapp)
