'''TM Nodes'''

from glob import glob
import os
import sys
from shutil import copyfile
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

_UPLOADS = os.path.join(mainapp.root_path, 'blueprints/nodes/uploads/')

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
    manifests = { 'manifest' : [] }
    if not _data[name]:
        manifests['manifest'] = ['No manifests uploaded yet.']
    else:
        for manifest in _data[name]:
            manifests['manifest'].append(os.path.basename(manifest))
    manifests['manifest'] = '\n'.join(manifests['manifest'])
    return render_template(
        _ERS_element + '.tpl',
        label=__doc__,
        name=name,
        itemdict=manifests)

###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/api/%s/' % _ERS_element, methods=('GET', ))
def get_all():
    nodes = list(_data.keys())
    response = jsonify( { 'node' : nodes } )
    response.status_code = 200
    return response


@BP.route('/api/%s/<name>' % _ERS_element, methods=('GET', ))
def api_node(name=None):
    if name not in _data:
        response = jsonify({ 'error': '"%s" node doesn\'t exist! ' })
        response.status_code = 404
        return response
    response = jsonify({ 'manifest' : _data[name] })
    response.status_code = 404
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

        copy_from = os.path.join(manifest.dirpath, manifest.basename)
        copy_to = '%s/%s/%s' % (_UPLOADS, nodenum, manifest.basename)
        copyfile(copy_from, copy_to)

        return jsonify({'success': 'manifest "%s" is set to node "%s".' % (manifest.basename, nodenum)})
    except BadRequest as e:
        response = e.get_response()
    except (AssertionError, ValueError) as e:
        response = jsonify({ 'error': str(e) })
    response.status_code = err_status
    return response


###########################################################################


def load_data():
    global _data
    _data = {}

    for root, dirs, files in os.walk(_UPLOADS):
        for dirname in dirs:
            node_path = os.path.join(root, dirname)
            _data[node_path] = glob('%s/%s/*.json' % (root, dirname))


# A singleton without a class
if '_data' not in locals():
    _data = None
    load_data()
