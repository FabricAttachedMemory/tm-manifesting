'''TM Nodes'''

from glob import glob
import json
import os
import sys
import shlex
import subprocess
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
    nodes_info = _load_data()
    if not nodes_info:              # FIXME: This is not a correct indentification of the node binding
        response = jsonify( { 'No Content' : 'There are no manifests associated with any nodes.' } )
        response.status_code = 204
        return response

    response = jsonify( { 'mappings' : nodes_info } )
    response.status_code = 200
    return response


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('GET', ))
def get_node_bind_info(node_coord=None):
    """
        List status json of the manifest binded to the node.
    """
    if not BP.nodes[node_coord]:
        return make_response('The specified node does not exist.', 404)

    result = get_node_status(node_coord)
    if result is None:
        return make_response('No Content', 204)

    return make_response(jsonify(result), 200)


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('DELETE', ))
def delete_node_binding(node_coord):
    """
    """
    if node_coord not in BP.node_coords:
        return make_response('The specified node does not exist.', 404)

    return make_response('Stay put. It will be implemented soon.', 501)

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
        resp_status = 409   # Conflict
        assert get_node_status(node_coord) is None, 'Node is occupied. Remove binding before assigning a new one.'

        resp_status = 413
        assert int(request.headers['Content-Length']) < 200, 'Content is too long! Max size is 200 characters.'

        resp_status = 400       # if failed at this point, then it is a server error.
        # Validate requested manifest exists.
        contentstr = request.get_data().decode()
        req_body = request.get_json(contentstr)

        manname = req_body['manifest']  # can have path in it

        manifest = BP.manifest_lookup(manname)
        resp_status = 404
        assert (manifest is not None) and node_coord in BP.node_coords, "The specified node or manifest does not exist."

        response = build_node(manifest, node_coord)
    except BadRequest as e:
        response = make_response(e.get_response(), resp_status)
    except (AssertionError, ValueError) as err:
        response = make_response(str(err), resp_status)

    return response

###########################################################################


def build_node(manifest, node_coord):
    """
        Build Process to Generate a custom filesystem image based of the provided manifset.

    :param 'manifest': [cls] manifest class of the 99-manifest/blueprint.py
    :param 'node_coord': [int\str] node number or name to generate filesystem image for.
    :return: flask's response data.
    """
    sys_imgs = BP.config['FILESYSTEM_IMAGES']
    golden_tar = BP.config['GOLDEN_IMAGE']

    if not os.path.exists(golden_tar):
        return make_response('Can not generate image! No "Golden Image" found!' % node_coord, 505)

    # ----------------------- Variables
    node_dir = os.path.join(sys_imgs,
                    BP.nodes[node_coord][0].hostname)   # place to build FS image at.
    tftp_node_dir = BP.config['TFTP_IMAGES'] + '/' +\
                    BP.nodes[node_coord][0].hostname    # place for PXE to pickup FS img from.
    node_hostname = BP.nodes[node_coord][0].hostname    # we except to find only one occurance of node_coord.
    custom_tar = os.path.normpath(node_dir + '/untar/') # path for FS img 'untar' folder to mess with.

    response = make_response('The manifest for the specified node has been set.', 201)

    if glob(tftp_node_dir + '/*.cpio'):
        response = make_response('The manifest for the specified node has been changed.', 200)

    # ------------------------- DRY RUN
    if BP.config['DRYRUN']:
        return response
    # ---------------------------------

    try:
        if not os.path.isdir(node_dir): # create directory to save generated img into.
            os.makedirs(node_dir)
    except (EnvironmentError):
        return make_response('Failed to create "%s"!' % node_dir, 505)

    # prepare FS environment to customize - untar into node's folder of manifesting server.
    custom_tar = customize_node.untar(golden_tar, destination=custom_tar)

    build_args = {
            'fs-image' : custom_tar,
            'hostname' : node_hostname,
            'tftp' : tftp_node_dir,
            'verbose' : BP.VERBOSE,
            'debug' : BP.DEBUG,
            'packages' : manifest.thedict['packages'],
            'manifest' : manifest.namespace
    }

    cmd_args = []
    for key, val in build_args.items():
        cmd_args.append('--%s %s' % (key, val))
    cmd = os.path.dirname(__file__) + '/node_builder/customize_node.py ' + ' '.join(cmd_args)
    cmd = shlex.split(cmd)

    try:
        _ = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except subprocess.SubprocessError as err:       # TSNH =)
        return make_response('Failed to start node binding process.', 418)

    manifest_tftp_file = manifest.namespace.replace('/', '.')
    customize_node.copy_target_into(manifest.fullpath, tftp_node_dir + '/' + manifest_tftp_file)

    return response

###########################################################################
_data = None # node <-> manifest bindings

def get_node_status(node_coord):
    """
        Scan tftp/images/{hostname} folder for "status.json" that is generated
    by node_builder/customize_node.py script. This file contatins information
    about the Node binding status that Comply with ERS specs (Section 8.6)

    :param 'node_coord': [str] noode full coordinate string.
    :return: [dict] values that describes node's state (status, message, manifest).
             (ERS document section 8.6)
    """
    node_location = BP.config['TFTP_IMAGES'] + '/' + BP.nodes[node_coord][0].hostname
    status_file = node_location + '/' + 'status.json'
    if not os.path.isdir(node_location):
        return None

    if not os.path.exists(status_file):
        return None

    status = {}
    try:
        with open(status_file, 'r') as file_obj:
            status = json.loads(file_obj.read())
    except ValueError as err:       # TCNH =)
        status['message'] = 'Failed to parse status file. Exception Error: %s ' % str(err)
        status['manifest'] = 'unknown'
        status['status'] = 'error'

    return status


def _load_data():
    """
        Scan tftp/images folder for known hostnames and read its status.json
    file. Save this data into a dictionary and return it to the user.

    :return: [dict] node_coordinate - node_status key value pair of the current
            status of the nodes.
    """
    result = {}
    for node in BP.nodes:
        node_status = get_node_status(node.coordinate)
        if node_status:
            result[node.coordinate] = node_status
    return result


def _manifest_lookup(name):
    # blueprints lookup has to be deferred until all are registered
    if name:
        name = name.strip('/')
    return BP.blueprints['manifest'].lookup(name)

###########################################################################


def register(mainapp):  # take what you like and leave the rest
    # Do some shortcuts
    global _data
    BP.config = mainapp.config
    BP.nodes = BP.config['tmconfig'].nodes
    BP.node_coords = frozenset([node.coordinate for node in BP.nodes])
    BP.blueprints = mainapp.blueprints
    BP.manifest_lookup = _manifest_lookup
    BP.binding = BP.config['NODE_BINDING'] # json file of all the Node to Manifest bindings.
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _data = _load_data()
