'''TM Nodes'''

from glob import glob
import os
import sys
from shutil import copyfile
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify
from werkzeug.exceptions import BadRequest

import img_builder

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
# @BP.route('/%s/<name>' % _ERS_element)
def node():
    return render_template(
        _ERS_element + '_all.tpl',
        label=__doc__,
        keys=sorted(_data.keys()),
        url_base=request.url)


@BP.route('/%s/<name>' % _ERS_element)
def node_name(name=None):
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

####################### API (PUT) ###############################

@BP.route('/api/%s/<nodenum>' % _ERS_element, methods=('PUT', ))
def api_nodenum(nodenum=None):
    try:
        err_status = 413
        assert int(request.headers['Content-Length']) < 200, 'Too big'

        # Validate requested manifest exists.
        contentstr = request.get_data().decode()
        manifest = request.get_json(contentstr)
        cfg = manifest.get('config', None)
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

        manifest_path = os.path.join(manifest.dirpath, manifest.basename)
        response = customize_image(manifest_path, nodenum, cfg=cfg)

        return jsonify({'success': 'manifest "%s" is set to node "%s".' % (manifest.basename, nodenum)})
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
    sys_imgs = mainapp.config['SYS_IMGS']
    golden = mainapp.config['GOLDEN_IMG']

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


def load_data():
    global _data
    _data = {}

    for root, dirs, files in os.walk(_UPLOADS):
        for dirname in dirs:
            node_path = os.path.join(root, dirname)
            node_path = os.path.normpath(node_path)
            json_pattern = os.path.normpath('%s/%s/*.json' % (root, dirname))
            _data[dirname] = glob(json_pattern)


# A singleton without a class
if '_data' not in locals():
    _data = None
    load_data()
