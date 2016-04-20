'''L4TM packages'''

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

# import blueprints_base  # still have not figured out how relative imports work.

_ERS_element = 'images'

# Mobius circular worked for a while.  I like this better.
mainapp = sys.modules['__main__'].mainapp

# See the README in the main templates directory.
BP = Blueprint(
    _ERS_element,
    __name__,
    template_folder='%s/%s' % (mainapp.root_path, mainapp.template_folder)
    )

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

def load_data():
    # https://github.com/raumkraut/python-debian/blob/master/README.deb822

    global _data
    _data = {}
    sys_img_dir = mainapp.config['SYSTEM_IMAGES_DIR']

    for abs_path, dirname, files in os.walk(sys_img_dir):
        for filename in fnmatch.filter(files, '*.tar'):
            _data[filename] = os.path.join(abs_path, filename)

    BP.filter = filter     # So manifest can see it


def filter(imgs):    # Maybe it's time for a class
    return [ sysimg for sysimg in imgs if sysimg not in _data ]


def data_to_json():
    result = defaultdict(list)
    for img_name in _data.keys():
        if 'golden' in img_name:
            result['golden'].append(img_name)
        else:
            result['custom'].append(img_name)
    return jsonify({'sys-image' : result })


# A singleton without a class
if '_data' not in locals():
    _data = None
    load_data()
