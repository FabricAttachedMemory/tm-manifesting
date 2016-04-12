'''L4TM packages'''

import gzip
import os
import requests as HTTP_REQUESTS
import sys

from debian.deb822 import Packages
from io import BytesIO, StringIO
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify

_ERS_element = 'package'

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
@BP.route('/%s/<name>' % _ERS_element)
def webpage(name=None):

    if name is None:
        return render_template(
            _ERS_element + '_all.tpl',
            label=__doc__,
            keys=sorted(_data.keys()),
            url_base=request.url)

    return render_template(
        _ERS_element + '.tpl',
        label=__doc__,
        name=name,
        itemdict=_data[name])

###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/api/%s/' % _ERS_element)
@BP.route('/api/%s/<name>' % _ERS_element)
def api(name=None):
    if name is None:
        packages = [ ]
        for pkg in _data.values():
            tmpdict = {
                'package': pkg['Package'],
                'version': pkg['Version'],
                'description': pkg['Description']
            }
            packages.append(tmpdict)
        return jsonify({ 'package': packages })

    pkg = _data.get(name, None)
    if pkg is None:
        return jsonify({ 'error': 'No such package "%s"' % name })
    for tag in ('Depends', 'Tags'):
        if tag in pkg and False:
            set_trace()
            pkg[tag] = pkg[tag].split(', ')
    return jsonify(pkg)

    return

###########################################################################


def load_data():
    # https://github.com/raumkraut/python-debian/blob/master/README.deb822

    global _data
    mirror = mainapp.config['L4TM_MIRROR']
    release = mainapp.config['L4TM_RELEASE']
    repo = '%s/dists/%s/%%s/%%s/Packages.gz' % (mirror, release)

    _data = { }
    for area in mainapp.config['L4TM_AREAS']:
        for arch in ('binary-all', 'binary-arm64'):
            print('---------- %s/%s/Packages.gz...' % (area, arch), end='')
            sys.stdout.flush()
            pkgresp = HTTP_REQUESTS.get(repo % (area, arch))
            print('%s bytes' % pkgresp.headers['content-length'])

            print('Uncompressing...', end='')
            sys.stdout.flush()
            unzipped = gzip.decompress(pkgresp.content) # bytes all around
            print('%s bytes' % len(unzipped))

            print('Parsing packages data...', end='')
            sys.stdout.flush()
            unzipped = BytesIO(unzipped)    # the next step needs read()
            tmp = [ src for src in Packages.iter_paragraphs(unzipped) ]
            _data.update(dict((pkg['Package'], pkg) for pkg in tmp))

    BP.filter = filter     # So manifest can see it


def filter(packages):    # Maybe it's time for a class
    return [ pkg for pkg in packages if pkg not in _data ]


# A singleton without a class
if '_data' not in locals():
    _data = None
    load_data()
