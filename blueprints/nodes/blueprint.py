'''TM Nodes'''

from glob import glob
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
    try:
        err_status = 413
        assert int(request.headers['Content-Length']) < 200, 'Too big'
        contentstr = request.get_data().decode()
        manifest = request.get_json(contentstr)
        manname = manifest['manifest']  # can have path in it
        manifest = mainapp.blueprints['manifest'].lookup(manname)
        err_status = 404
        assert manifest is not None, 'no such manifest ' + manname
        node = int(nodenum)
        err_status = 400
        assert 1 <= node <= 80, 'Value out of range'
        return jsonify({'status': 'you got lucky'})
    except BadRequest as e:
        response = e.get_response()
    except (AssertionError, ValueError) as e:
        response = jsonify({ 'error': str(e) })
    response.status_code = err_status
    return response


###########################################################################


def load_data():
    global _data

    nodes_dir = "%s/nodes/" % (mainapp.config['SYSTEM_IMAGES_DIR'])

    for root, dirs, files in os.walk(nodes_dir):
        for dirname in dirs:
            _data[dirname] = glob('%s/%s/*.json' % (root, dirname, dirname))

    _data = { }

# A singleton without a class
if '_data' not in locals():
    _data = None
    load_data()
