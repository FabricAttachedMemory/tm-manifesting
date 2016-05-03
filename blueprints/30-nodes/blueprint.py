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

@BP.route('/api/%s/<path:nodenum>' % _ERS_element, methods=('PUT', ))
def api_nodenum(nodenum=None):
    try:
        err_status = 413
        assert int(request.headers['Content-Length']) < 200, 'Too big'

        # Validate requested manifest exists.
        contentstr = request.get_data().decode()
        manifest = request.get_json(contentstr)
        cfg = manifest.get('config', None)
        manname = manifest['manifest']  # can have path in it
        manifest = BP.manifest_lookup(manname)
        err_status = 404
        assert manifest is not None, 'no such manifest ' + manname

        _data[nodenum] = manifest.basename
        save(_data, BP.binding)
        manifest_path = os.path.join(manifest.dirpath, manifest.basename)

        img_resp = customize_image(manifest_path, nodenum, cfg=cfg)
        return jsonify(img_resp)

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
    golden_tar = BP.config['GOLDEN_IMG']

    if not os.path.exists(golden_tar):
        return { 'error' : 'Can not customize image for node "%s"! No "Golden Image" found!' }

    img_name = os.path.basename(manifest).split('.json')[0]
    node_dir = os.path.join(sys_imgs, node)

    try:
        if not os.path.isdir(node_dir): # directory to save generated img into.
            os.makedirs(node_dir)
    except (EnvironmentError):
        return { 'error' : 'Couldn\'t create destination folder for the image at: %s' % (node_dir) }

    # absolute path (with a file name) to where Golden image .tar file will be coppied to
    custom_tar = os.path.normpath('%s/%s.tar' % (node_dir, img_name))
    try:
        copyfile(golden_tar, custom_tar)
    except (EnvironmentError):
        return { 'error' : 'Couldn\'t copy golden image into node\'s directory "%s" >> "%s"' % (golden_tar, custom_tar) }

    status = img_builder.default_cfg(manifest, custom_tar)
    if status['status'] is 'success':
        return { 'success' : 'Manifest "%s" is set to node "%s"' %
                (os.path.basename(manifest), node) }
    else:
        return { status['status'] : status['message'] }

###########################################################################
_data = None    # node <-> manifest bindings


def save(content, destination):
    """
        Save json content into destination file.
    Note: file will be removed before saving into it - e.g. overwritten with a new data.

    :param 'content': [str or dict] data to be saved.
    :param 'destination': [str] file to save into.
    """
    if isinstance(content, dict):
        content = json.dumps(content, indent=4)

    new_file = '%s.new' % (destination)
    try:
        with open(new_file, 'w+') as file_obj: # if that fails, shouldn't bother to rename then.
            file_obj.write(content)
        os.rename(new_file, destination)
    except IOError as error:
        print('Couldn\'t save file into "%s"' % (destination), file=sys.stderr)
        return 1
    return 0


def _load_data():
    """
        Load json data from file and return a dictionary.

    :param 'target_file': [str] path to a file to load data from.
    :return: [dict] data parsed from a json string of the 'target_file'
    """
    global _data
    _data = {}
    try:
        with open(BP.binding, 'r+') as file_obj:
            _data = json.loads(file_obj.read())
    except IOError as err:
        print ('Couldn\'t load "%s"' % (BP.binding), file=sys.stderr)

    for node in _data.keys():
        if node not in BP.coords:
            _data.remove(node)

    return _data


def _manifest_lookup(name):
    # blueprints lookup has to be deferred until all are registered
    return BP.blueprints['manifest'].lookup(name)


def register(mainapp):  # take what you like and leave the rest
    # Do some shortcuts
    BP.config = mainapp.config
    BP.nodes = BP.config['tmconfig'].nodes
    BP.coords = [node.coordinate for node in BP.nodes]
    BP.blueprints = mainapp.blueprints
    BP.manifest_lookup = _manifest_lookup
    BP.binding = '%s/binding.json' % (os.path.dirname(__file__)) # json file of all the Node to Manifest bindings.
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _load_data()
