'''TM Nodes'''

from glob import glob
import json
import os
import sys
from shutil import copyfile
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify, make_response
from werkzeug.exceptions import BadRequest

from .node_builder import customize_node # programmatic import in main requires this

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

@BP.route('/api/%ss/' % _ERS_element, methods=('GET', ))
def get_all_nodes():
    """
        List all nodes coordinates known to the server.
    """
    response = jsonify( { 'nodes' : list(BP.node_coords) } )
    response.status_code = 200
    return response


@BP.route('/api/%s/' % _ERS_element, methods=('GET', ))
def get_all_bindings():
    """
        List all node binded to a manifest with its status (ready, building or error).
    """
    if len(_data) == 0:
        response = jsonify( { 'No Content' : 'There are no manifests associated with any nodes.' } )
        response.status_code = 204
        return response

    nodes_info = {}
    for node_coord, manname in _data.items():
        nodes_info[node_coord] = {}

        nodes_info[node_coord]['manifest'] = manname
        nodes_info[node_coord]['status'] = 'Unknown'
        nodes_info[node_coord]['message'] = 'Status not implemented.'

    response = jsonify( { 'mappings' : nodes_info } )
    response.status_code = 200
    return response


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('GET', ))
def get_node_bind_info(node_coord=None):
    """
        List status json of the manifest binded to the node.
    """
    if node_coord not in BP.node_coords:
        response = jsonify({ 'Not Found' : 'The specified node does not exist.' })
        response.status_code = 404
        return response

    manname = _data.get(node_coord, None)
    manifest = BP.manifest_lookup(manname)
    if not manifest:
        response = jsonify( { 'No Content' : 'There is no manifest associated with the specified node.' } )
        response.status_code = 204
        return response

    result = {}
    result['manifest'] = manname
    result['status'] = 'Unknown'
    result['message'] = 'Status not implemented.'

    response = jsonify( result )
    response.status_code = 200
    return response

####################### API (PUT) ###############################

@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('PUT', ))
def bind_node_to_manifest(node_coord=None):
    """
        Generate a custom filesystem image for a provided node coordinate using
    a manifest specified in the request's body. The resulting FS image will be
    placed at the server's location for PXE to pickup. This location is determined
    by the node's hostname, e.g. tftp/arm64/hostname1/

    :param 'node_coord': full node's coordinate with it's rack number, enclouse and etc.
    """
    try:
        resp_status = 413
        assert int(request.headers['Content-Length']) < 200, 'Content is too long! Max size is 200 characters.'

        # Validate requested manifest exists.
        contentstr = request.get_data().decode()
        req_body = request.get_json(contentstr)

        manname = req_body['manifest']  # can have path in it

        manifest = BP.manifest_lookup(manname)
        resp_status = 404
        assert (manifest is not None) and node_coord in BP.node_coords, "The specified node or manifest does not exist."

        _data[node_coord] = manifest.prefix + '/' + manifest.basename
        save(_data, BP.binding)

        img_resp = build_node(manifest, node_coord)

        response = jsonify(img_resp)
    except BadRequest as e:
        resp_status = 500
        response = e.get_response()
    except (ValueError,AssertionError) as err:
        response = jsonify( { 'Error' : str(err) } )

    response.status_code = resp_status
    return response

###########################################################################


def build_node(manifest, node_coord):
    """
        Generate a custom filesystem image based of the provided manifset.

    :param 'manifest': [str] absolute path to manifest.json file.
    :param 'node_coord': [int\str] node number or name to generate filesystem image for.
    :return: [json str] success or error status.
    """
    sys_imgs = BP.config['FILESYSTEM_IMAGES']
    golden_tar = BP.config['GOLDEN_IMAGE']
    if not os.path.exists(golden_tar):
        return { 'error' : 'Can not customize image for node "%s"! No "Golden Image" found!' % node_coord }

    if BP.config['DRYRUN']:
        return { 'success' : 'Manifest [%s] is set to node [%s]' %
                (os.path.basename(manifest.basename), node_coord) }

    node_dir = os.path.join(sys_imgs, BP.nodes[node_coord][0].hostname)

    try:
        if not os.path.isdir(node_dir): # directory to save generated img into.
            os.makedirs(node_dir)
    except (EnvironmentError):
        return { 'error' : 'Couldn\'t create destination folder for the image at: %s' % (node_dir) }

    # absolute path (with a file name) to where Golden image .tar file will be coppied to
    custom_tar = os.path.normpath(node_dir + '/untar/')
    # prepare the environment to mess with - untar into node's coord folder of manifesting server.
    custom_tar = customize_node.untar(golden_tar, destination=custom_tar)

    #tftp_arm = BP.config['TFTP'] + '/arm64/enc%s/node%s/' % (BP.nodes[node_coord][0].enc, BP.nodes[node_coord][0].node)
    tftp_node_dir = BP.config['TFTP_IMAGES'] + '/' + BP.nodes[node_coord][0].hostname

    # customization magic (not so much though).
    node_hostname = BP.nodes[node_coord][0].hostname  # we except to find only one occurance of node_coord

    status = customize_node.execute(
        custom_tar, hostname=node_hostname, tftp=tftp_node_dir,
        package_list=manifest.thedict['packages'],
        verbose=BP.VERBOSE, debug=BP.DEBUG
        )

    if status['status'] == 'success':
        return { 'success' : 'Manifest [%s] is set to node [%s]' %
                (os.path.basename(manifest.basename), node_coord) }
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


def _manifest_lookup(name):
    # blueprints lookup has to be deferred until all are registered
    return BP.blueprints['manifest'].lookup(name)


def register(mainapp):  # take what you like and leave the rest
    # Do some shortcuts
    BP.config = mainapp.config
    BP.nodes = BP.config['tmconfig'].nodes
    BP.node_coords = frozenset([node.coordinate for node in BP.nodes])
    BP.blueprints = mainapp.blueprints
    BP.manifest_lookup = _manifest_lookup
    BP.binding = BP.config['NODE_BINDING'] # json file of all the Node to Manifest bindings.
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _load_data()
