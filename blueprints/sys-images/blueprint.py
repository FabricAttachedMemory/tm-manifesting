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

import blueprints_base  # still have not figured out how relative imports work.

_ERS_element = 'sys-image'

# Mobius circular worked for a while.  I like this better.
mainapp = sys.modules['__main__'].mainapp

# See the README in the main templates directory.
BP = Blueprint(
    _ERS_element,
    __name__,
    template_folder='%s/%s' % (mainapp.root_path, mainapp.template_folder)
    )

###########################################################################


class SysImagesBlueprint(blueprints_base.Blueprint):
    """
        This class manages "manifesting/image/" and "manifesting/api/image/ " interaction.
    """

    def __init__(self, cfg={}):
        super().__init__(cfg=cfg)
        self.load_data()

    def load_data(self):
        """
            Walk through folder of TARed file images located on the server and save it in the
        self.data dictionary as a "file_name" - "absolute_path/.tar" pair.
        """
        for abs_path, dirname, filename in os.walk(self.config['SYSTEM_IMAGES_DIR']):
            for filename in fnmatch.filter(filename, '*.tar'):
                self.data[filename] = os.path.join(abs_path, filename)
        return self.data

    def jsonify(self):
        result = defaultdict(list)
        for img_name in self.data.keys():
            if 'golden' in img_name:
                result['golden'].append(img_name)
            else:
                result['custom'].append(img_name)
        return jsonify({'sys-image' : result })


SysImagesBp = SysImagesBlueprint(cfg=mainapp.config)
BP.filter = SysImagesBp.filter_out

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/%s/' % _ERS_element)
def webpage_show_all_tar(name=None):
    return render_template(
        _ERS_element + '_all.tpl',
        label=__doc__,
        keys=sorted(SysImagesBp.keys),
        url_base=request.url)


@BP.route('/%s/<name>' % _ERS_element)
def webpage_download_tar(name):
    file_location = SysImagesBp.lookup(name)
    file_name = os.path.basename(file_location)
    return send_file(file_location,
                    as_attachment=True,
                    attachment_filename=file_name)

###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/api/%s/' % _ERS_element)
def api():
    return SysImagesBp.jsonify()


@BP.route('/api/%s/<name>' % _ERS_element)
def api_download(name=None):
    return webpage_download_tar(name)

###########################################################################


"""
def load_data():
    # https://github.com/raumkraut/python-debian/blob/master/README.deb822

    global _data
    _data = {}
    sys_img_dir = mainapp.config['SYSTEM_IMAGES_DIR']

    for abs_path, dirname, filename in os.walk(sys_img_dir):
        for filename in fnmatch.filter(filename, '*.tar'):
            _data[filename] = os.path.join(abs_path, filename)

    BP.filter = filter     # So manifest can see it


def filter(packages):    # Maybe it's time for a class
    return [ pkg for pkg in packages if pkg not in _data ]


# A singleton without a class
if '_data' not in locals():
    _data = None
    load_data()
"""
