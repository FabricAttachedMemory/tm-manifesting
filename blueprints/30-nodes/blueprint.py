'''TM Nodes'''

from glob import glob
import json
import os
import sys
from shutil import copyfile
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify, make_response
from werkzeug.exceptions import BadRequest

from . import img_builder   # programmatic import in main requires this

_ERS_element = 'node'

# See the README in the main templates directory.
BP = Blueprint(_ERS_element, __name__)

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/%s/' % _ERS_element)
def node():
    return render_template(
        _ERS_element + '_all.tpl',
        label=__doc__,
        nodes=BP.nodes,
        url_base=request.url)


@BP.route('/%s/<path:name>' % _ERS_element)
def node_name(name=None):
    manifest = BP.manifest_lookup('ZHOPA')
    try:
        node = BP.nodes[name][0]
        MACaddress = node.soc.socMacAddress
        return render_template(
            _ERS_element + '.tpl',
            label=__doc__,
            node=node,
            manifest=_data.get(name, '(no binding)')
        )
    except Exception as e:
        return make_response('Kaboom', 404)

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

####################### API (PUT) ###############################

@BP.route('/api/%s/<path:node>' % _ERS_element, methods=('PUT', ))
def api_nodenum(nodenum=None):
    try:
        err_status = 413
        assert int(request.headers['Content-Length']) < 200, 'Too big'

        # Validate requested manifest exists.
        contentstr = request.get_data().decode()
        manifest = request.get_json(contentstr)
        cfg = manifest.get('config', None)
        manname = manifest['manifest']  # can have path in it
        manifest = BP.lookup_manifest(manname)
        err_status = 404
        assert manifest is not None, 'no such manifest ' + manname

        # Everything from here needs work

        #copy_from = os.path.join(manifest.dirpath, manifest.basename)
        #copy_to = '%s/%s/%s' % (BP.UPLOADS, nodenum, manifest.basename)
        #copyfile(copy_from, copy_to)

        _data[nodenum] = manifest.basename
        set_trace()
        #manifest_path = os.path.join(manifest.dirpath, manifest.basename)
        #response = customize_image(manifest_path, nodenum, cfg=cfg)

        return jsonify({"success": "manifest '%s' is set to node '%s'" % (manifest.basename, nodenum)})
    except BadRequest as e:
        response = e.get_response()
    except (AssertionError, ValueError) as e:
        response = jsonify({ 'error': str(e) })
    response.status_code = err_status
    return response

###########################################################################

def customize_image(manifest, node, cfg=None):
    """
        Generate a custom filesystem image based of the provided manifset.

    :param 'manifest': [str] absolute path to manifest.json file.
    :param 'node': [int\str] node number or name to generate filesystem image for.
    :return: [json str] success or error status.
    """
    sys_imgs = BP.config['SYS_IMGS']
    golden = BP.config['GOLDEN_IMG']

    if not os.path.exists(golden):
        return { 'error' : 'Can not customize image for node "%s"! No "Golden Image" found!' }

    img_name = os.path.basename(manifest).split('.json')[0]
    node_dir = os.path.join(sys_imgs, node)

    if not os.path.isdir(node_dir):
        os.mkdir(node_dir)

    img_location = os.path.normpath('%s/%s/' % (node_dir, img_name))
    if not os.path.isdir(img_location):
        os.mkdir(img_location)

    # absolute path (with a file name) to where Golden image will be coppied to
    tar_file = os.path.normpath('%s/%s.tar' % (img_location, img_name))
    copyfile(golden, tar_file)

    status = img_builder.default_cfg(manifest, tar_file)
    if status == 0:
        return { 'success' : 'Filesystem image for node "%s" was generated.' % (node) }
    else:
        return { 'error' : 'Something went wrong in the process of generating filesystem image for node "%s" ' % (node) }

###########################################################################

_data = None    # node <-> manifest bindings

def _load_data():
    global _data

    if not os.path.exists(BP.binding):
        with open(BP.binding, 'w+') as file_obj:
            file_obj.write('{}')

    with open(BP.binding, 'r+') as file_obj:
        _data = json.loads(file_obj.read())


def save_binding(content):
    with open(BP.binding, 'w+') as file_obj:
        file_obj.write(content)


def _manifest_lookup(name):
    # blueprints lookup has to be deferred until all are registered
    return BP.blueprints['manifest'].lookup(name)


def register(mainapp):  # take what you like and leave the rest
    # Do some shortcuts
    BP.config = mainapp.config
    BP.nodes = BP.config['tmconfig'].nodes
    BP.binding = '%s/binding.json' % (os.path.dirname(__file__)) # json file of all the Node to Manifest bindings.
    BP.blueprints = mainapp.blueprints
    BP.manifest_lookup = _manifest_lookup
    BP.pickle = os.path.join(mainapp.root_path, 'blueprints/nodes/node2manifest.bin/')
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _load_data()
