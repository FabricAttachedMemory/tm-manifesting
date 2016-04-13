'''TM Nodes'''

import os
import sys
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify

_ERS_element = 'node'

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
    response = jsonify({ 'error': 'API GET not implemented' })
    response.status_code = 501
    return response

###########################################################################


def load_data():
    global _data

    _data = { }

# A singleton without a class
if '_data' not in locals():
    _data = None
    load_data()
