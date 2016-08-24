#!/usr/bin/python3
'''TM Nodes'''
from glob import glob
import json
import os
import sys
import time
from shutil import copyfile
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify
from flask import make_response, send_from_directory
from werkzeug.exceptions import BadRequest

from tmms.utils.utils import piper
from tmms.utils import customize_node

# programmatic import in main requires this form
#from .node_builder import customize_node

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
    '''name will never have a leading / but now always needs one.'''
    name = '/' + name
    try:
        node = BP.nodes[name][0]
        ESPURL = None    # testable value in Jinja2
        status = get_node_status(name)
        if status is not None and status['status'] == 'ready':
            ESPpath = '%s/%s/%s.ESP' % (
                BP.config['TFTP_IMAGES'], node.hostname, node.hostname)
            if os.path.isfile(ESPpath):
                prefix = request.url.split(_ERS_element)[0]
                ESPURL = '%s%s/ESP/%s' % (prefix, _ERS_element, node.hostname)
        return render_template(
            _ERS_element + '.tpl',
            label=__doc__,
            node=node,
            status=status,
            ESPURL=ESPURL
        )
    except Exception as e:
        return make_response('Kaboom: %s' % str(e), 404)


@BP.route('/%s/ESP/<path:hostname>' % _ERS_element)
def node_ESP(hostname):
    filename = hostname + '.ESP'
    ESPdir = '%s/%s' % (BP.config['TFTP_IMAGES'], hostname)

    return send_from_directory(
        ESPdir,                                     # required #1
        filename,                                   # required #2
        as_attachment=True,                         # os.path.basename
        mimetype='application/x-raw-disk-image',    # dialogs say "ESP file"
        cache_timeout=0)                            # Not in mainapp.config

###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/api/%ss/' % _ERS_element, methods=('GET', ))
def get_all_nodes():
    """
        List all nodes coordinates known to the server.
    """
    response = jsonify({'nodes': list(BP.node_coords)})
    response.status_code = 200
    return response


@BP.route('/api/%s/' % _ERS_element, methods=('GET', ))
def get_all_bindings():
    """
        List all nodes, their manifest bindings, and status
        (ready, building or error).
    """
    nodes_info = _load_data()
    if not nodes_info:  # FIXME: This is not a correct id of the node binding
        response = jsonify({
            'No Content': 'There are no manifests associated with any nodes.'})
        response.status_code = 204
        return response

    response = jsonify({'mappings': nodes_info})
    response.status_code = 200
    return response


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('GET', ))
@BP.route('/api/%s//<path:node_coord>' % _ERS_element, methods=('GET', ))
def get_node_bind_info(node_coord=None):
    """
        List status json of the manifest bound to the node.
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


def node_coord2image_dir(node_coord):
    '''Calculate TFTP directory for kernel/FS from node coordinate/'''
    node_image_dir = BP.config['TFTP_IMAGES'] + '/' + \
        BP.nodes[node_coord][0].hostname
    assert os.path.isdir(node_image_dir), \
        'Missing directory "%s"' % node_image_dir
    return node_image_dir


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('DELETE', ))
@BP.route('/api/%s//<path:node_coord>' % _ERS_element, methods=('DELETE', ))
def delete_node_binding(node_coord):
    """
        Remove Node to Manifest binding. Find node's folder in the TFTP
    directory by its hostname and clean out the content. Thus the next
    reboot will fail.

    :param 'node_coord': full node's coordinate to unbind Manifest from.
    """
    # Two rules invoke Postel's Law of liberal reception.  Either way,
    # we need to add leading /.
    node_coord = '/' + node_coord
    if node_coord not in BP.node_coords:
        return make_response('The specified node does not exist.', 404)

    try:
        node_image_dir = node_coord2image_dir(node_coord)
        for node_file in glob(node_image_dir + '/*'):
            os.remove(node_file)
    except OSError as err:
        return make_response('Failed to delete binding: %s' % err, 500)

    return make_response('Successful cleanup.', 204)

####################### API (PUT) ###############################


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('PUT', ))
@BP.route('/api/%s//<path:node_coord>' % _ERS_element, methods=('PUT', ))
def bind_node_to_manifest(node_coord=None):
    """
        Generate a custom filesystem image for a provided node coordinate
    using a manifest specified in the request's body. The resulting FS image
    will be placed at appropriate place under the TFTP hierarchy based on
    hostname.

    :param 'node_coord': absolute machine coordinate of the node
    """
    node_coord = '/' + node_coord   # Postel's Law, node_coord is naked.
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

    packages = manifest.thedict['packages']
    if packages:
        packages = ','.join(packages)
    else:
        packages = None     # sentinel for following loop
    tasks = manifest.thedict['tasks']
    if tasks:
        tasks = ','.join(tasks)
    else:
        tasks = None     # sentinel for following loop

    build_args = {
        'hostname':     hostname,
        'client_id':    client_id,
        'manifest':     manifest.namespace,     # FIXME: basename?
        'packages':     packages,
        'tasks':        tasks,
        'golden_tar':   golden_tar,
        'build_dir':    build_dir,
        'tftp_dir':     tftp_dir,
        'verbose':      BP.VERBOSE,
        'debug':        BP.DEBUG,
    }

    cmd_args = []
    for key, val in build_args.items():
        if val is not None:     # packages and tasks, default is None
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

    try:    # FIXME: instead of JIT, move this to setup_networking?
        os.makedirs(build_dir + '/ESP', exist_ok=True)
    except (EnvironmentError):
        return make_response('Failed to create "%s"!' % build_dir, 505)

    forked = os.fork()
    build_error = None
    print(' --- 30-node parent PID: %s' % (forked))
    if forked == 0:
        try:
            customize_node.execute(build_args)
        except Exception as err:
            print (' -- main fork error: %s' % (str(err)))
            #build_error = err
        print(' --- Blueprint\'s CHILD here! [%s]' % build_err)

    os.wait()
    if build_error is not None:
        return make_response('Node binding failed: %s' % str(build_error), 418)
    #customize_node.execute(build_args)

    # FIXME: move this to customize_node
    manifest_tftp_file = manifest.namespace.replace('/', '.')
    customize_node.copy_target_into(
        manifest.fullpath,
        tftp_dir + '/' + manifest_tftp_file)

    return response

###########################################################################


_data = None    # node <-> manifest bindings


def get_node_status(node_coord):
    """
        Scan tftp/images/{hostname} folder for "status.json" that is generated
    by node_builder/customize_node.py script. This file contatins information
    about the Node binding status that complies with ERS specs (Section 8.6)

    :param 'node_coord': [str] node full coordinate string.
    :return: [dict] values that describes node's state
             (status, message, manifest)  (ERS document section 8.6)
             None no status file (ie, node is unbound)
    """
    try:
        assert node_coord in BP.node_coords, 'Unknown node coordinate'
        node_image_dir = node_coord2image_dir(node_coord)   # can raise
        with open(node_image_dir + '/status.json', 'r') as file_obj:
            status = json.loads(file_obj.read())
    except FileNotFoundError as err:    # Unbound
        return None
    except Exception as err:       # TCNH =)
        status = {
            'message':  'Failed to parse status file: %s ' % str(err),
            'manifest': 'unknown',
            'status':   'error'
        }
    return status


def _load_data():
    """
        Scan tftp/images folder for known hostnames and read its status.json
    file. Save this data into a dictionary and return it to the user.

    :return: [dict] node_coordinate - node_status key value pair of the
        current status of the nodes.
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
    try:
        BP.nodes = BP.config['tmconfig'].allNodes
    except Exception:
        BP.nodes = BP.config['tmconfig'].nodes
    BP.node_coords = frozenset([node.coordinate for node in BP.nodes])
    BP.blueprints = mainapp.blueprints
    BP.manifest_lookup = _manifest_lookup
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _data = _load_data()
