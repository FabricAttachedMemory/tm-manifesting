#!/usr/bin/python3 -tt
'''TM Nodes'''
from glob import glob
import json
import os
import sys
import shlex
import subprocess
import time
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
@BP.route('/%s//<path:name>' % _ERS_element)    # Postel's law
def node_name(name=None):
    try:
        node = BP.nodes['/' + name][0]
        return render_template(
            _ERS_element + '.tpl',
            label=__doc__,
            node=node,
            manifest=_data.get(name, '(no binding)')
        )
    except Exception as e:
        return make_response('Kaboom: %s' % str(e), 404)

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
@BP.route('/api/%s//<path:node_coord>' % _ERS_element, methods=('GET', ))
def get_node_bind_info(node_coord=None):
    """
        List status json of the manifest binded to the node.
    """
    # Two rules invoke Postel's Law of liberal reception.  Either way,
    # we need to add leading /.
    node_coord = '/' + node_coord
    if not BP.nodes[node_coord]:
        return make_response('The specified node does not exist.', 404)

    result = get_node_status(node_coord)
    if result is None:
        return make_response('No Content', 204)

    return make_response(jsonify(result), 200)


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('DELETE', ))
@BP.route('/api/%s//<path:node_coord>' % _ERS_element, methods=('DELETE', ))
def delete_node_binding(node_coord):
    """
        Remove Node to Manifest binding. Find node's folder in the TFTP directory
    by its hostname and clean out the content. Thus, on the next node reboot, it
    will be not served by the TFTP.

    :param 'node_coord': full node's coordinate to unbinde Manifest from.
    """
    node_coord = '/' + node_coord
    if node_coord not in BP.node_coords:
        return make_response('The specified node does not exist.', 404)

    node_location = BP.config['TFTP_IMAGES'] + '/' + BP.nodes[node_coord][0].hostname
    if not os.path.isdir(node_location):        # Paranoia. That should never happened.
        return make_response('TFT doesn\'t serve requested node.', 404)

    try:
        for node_file in glob(node_location + '/*'):
            os.remove(node_file)
    except OSError as err:
        return make_response('Failed to delete binding due to OSError:\n%s' % err, 500)

    return make_response('Successful cleanup.', 204)

####################### API (PUT) ###############################


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('PUT', ))
@BP.route('/api/%s//<path:node_coord>' % _ERS_element, methods=('PUT', ))
def bind_node_to_manifest(node_coord=None):
    """
        Generate a custom filesystem image for a provided node coordinate using
    a manifest specified in the request's body. The resulting FS image will be
    placed at appropriate place under the TFTP hierarchy based on hostname.

    :param 'node_coord': absolute machine coordinate of the node
    """
    node_coord = '/' + node_coord
    try:
        resp_status = 409   # Conflict
        assert get_node_status(node_coord) is None, 'Node is already bound.'

        resp_status = 413
        assert int(request.headers['Content-Length']) < 200, \
            'Content is too long! Max size is 200 characters.'

        resp_status = 400
        # Validate requested manifest exists.
        contentstr = request.get_data().decode()
        req_body = request.get_json(contentstr)

        manname = req_body['manifest']  # can have path in it

        manifest = BP.manifest_lookup(manname)
        resp_status = 404
        assert manifest is not None, "The specified manifest does not exist."
        response = build_node(manifest, node_coord)
    except BadRequest as e:
        response = make_response(e.get_response(), resp_status)
    except (AssertionError, ValueError) as err:
        response = make_response(str(err), resp_status)

    return response

###########################################################################


def build_node(manifest, node_coord):
    """
        Generate a custom filesystem image based on the provided manifset.

    :param 'manifest': [cls] manifest class of the 99-manifest/blueprint.py
    :param 'node_coord': [int\str] node number or name.
    :return: flask's response data.
    """
    golden_tar = BP.config['GOLDEN_IMAGE']
    if not os.path.exists(golden_tar):
        return make_response('Missing "Golden Image"', 505)

    # each node gets its own set of dirs
    hostname = BP.nodes[node_coord][0].hostname
    sys_imgs = BP.config['FILESYSTEM_IMAGES']
    build_dir = os.path.join(sys_imgs, hostname)
    tftp_dir = BP.config['TFTP_IMAGES'] + '/' + hostname

    # See setup_grub.py on client ID.  Trust me.
    rack_prefix = node_coord.split('Enclosure')[0]
    client_id = rack_prefix + 'EncNum' + node_coord.split('EncNum')[1]

    build_args = {
            'hostname':     hostname,
            'client_id':    client_id,
            'manifest':     manifest.namespace, # FIXME: basename?
            'packages':     manifest.thedict['packages'],   # FIXME: tasks?
            'golden_tar':   golden_tar,
            'build_dir':    build_dir,
            'tftp_dir':     tftp_dir,
            'verbose':      BP.VERBOSE,
            'debug':        BP.DEBUG,
    }

    cmd_args = []
    for key, val in build_args.items():
        if val is not None:     # packages and tasks
            cmd_args.append('--%s %s' % (key, val))
    cmd = os.path.dirname(__file__) + \
          '/node_builder/customize_node.py ' + ' '.join(cmd_args)

    response = make_response(
        'Manifest set; image build initiated.', 201)

    if glob(tftp_dir + '/*.cpio'):
        response = make_response(
            'Existing manifest changed; image re-build initiated.', 200)

    # ------------------------- DRY RUN
    if BP.config['DRYRUN']:
        response.set_data(response.get_data().decode() + ' (DRY RUN)')
        print(cmd)      # Now you can cut/paste and run it by hand.
        # FIMXE: what about status.json?
        return response
    # ---------------------------------

    try:
        os.makedirs(build_dir, exist_ok=True)
    except (EnvironmentError):
        return make_response('Failed to create "%s"!' % build_dir, 505)

    cmd = shlex.split(cmd)
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        # Now that everything is in subprocess, this routine is FAST.
        # untar and gzip will take a minimum of five seconds. Be
        # completely sure the process really had time to start.
        time.sleep(3)
        assert p.poll() is None     # still running
    except (AssertionError, subprocess.SubprocessError) as err:    # TSNH =)
        stdout, stderr = p.communicate()
        return make_response('Node binding failed: %s' % stderr.decode(), 418)

    # FIXME: move this to customize_node
    manifest_tftp_file = manifest.namespace.replace('/', '.')
    customize_node.copy_target_into(
        manifest.fullpath,
        tftp_dir + '/' + manifest_tftp_file)

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
    assert node_coord in BP.node_coords, 'Unknown node coordinate'

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
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _data = _load_data()
