'''TM Nodes'''

import os
import sys
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify
from werkzeug.exceptions import BadRequest

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


@BP.route('/api/%s/<nodenum>' % _ERS_element, methods=('PUT', ))
def api_nodenum(nodenum=None):
    assert int(request.headers['Content-Length']) < 200, 'Too big'
    try:
        contentstr = request.get_data().decode()
        manifest = request.get_json(contentstr)
        nosuch = mainapp.blueprints['manifest'].filter(manifest['manifest'])
        assert not nosuch, 'no such manifest(s) ' + ', '.join(nosuch)
        node = int(nodenum)
        assert 1 <= node <= 80, 'Value out of range'
        return jsonify({'status': 'you got lucky'})
    except BadRequest as e:
        return e.get_response()
        return response
    except (AssertionError, ValueError) as e:
        response = jsonify({ 'error': str(e) })
        response.status_code = 406
        return response


###########################################################################


def load_data():
    global _data

    _data = { }

# A singleton without a class
if '_data' not in locals():
    _data = None
    load_data()
