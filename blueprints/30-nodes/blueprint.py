#!/usr/bin/python3
"""TM Nodes
 This blueprint handles "nodes" related routines to allow users to list all available
nodes in the manifesting-server network (defined by tmms config file), bind images
to nodes or unbind them.
"""
__author__ = "Zakhar Volchak, Rocky Craig"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Zakhar Volchak, Rocky Craig"
__email__ = "zach.bender@tutanota.com, rocky.craig@hpe.com"


import errno
import json
import os
import sys
import time

from argparse import Namespace
from glob import glob
from shutil import copyfile
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify
from flask import make_response, send_from_directory, redirect
from werkzeug.exceptions import BadRequest

from tmms.utils.utils import piper
from tmms.utils.logging import tmmsLogger
from .node_builder import customize_node

_ERS_element = 'node'

# See the README in the main templates directory.
BP = Blueprint(_ERS_element, __name__)

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/%s/' % _ERS_element)
def web_node_all():
    nodes_info = BP.nodes
    for node in nodes_info:
        status = get_node_status(node.coordinate)
        if status:
            node.manifest = status['manifest']
            node.status = status['status']

    return render_template(
        _ERS_element + '_all.tpl',
        label=__doc__,
        nodes=BP.nodes,
        base_url=request.url)


@BP.route('/%s/<path:name>' % _ERS_element, methods=('POST', ))
@BP.route('/%s//<path:name>' % _ERS_element, methods=('POST', ))
def web_node_button_action(name=None):
    # Either way, name has no leading slash.
    if 'unbind' in request.form:
        delete_node_binding(name)
    elif 'bind' in request.form:
        manname = request.form['manifest_sel']
        manifest = BP.manifest_lookup(manname)
        build_node(manifest, name)
    return redirect(request.base_url)   # Eliminates browser caching of POST


@BP.route('/%s/<path:name>' % _ERS_element)
@BP.route('/%s//<path:name>' % _ERS_element)    # Postel's law
def web_node_status(name=None):
    '''name will never have a leading / but now always needs one.'''
    name = '/' + name
    try:
        node = BP.nodes[name][0]
        ESPURL = None    # testable value in Jinja2
        ESPsizeMB = 0
        installsh = installlog = None
        status = get_node_status(name)
        if status is not None:
            if status['status'] == 'ready':
                ESPpath = '%s/%s/%s.ESP' % (
                    BP.config['TFTP_IMAGES'], node.hostname, node.hostname)
                if os.path.isfile(ESPpath):
                    prefix = request.url.split(_ERS_element)[0]
                    ESPURL = '%s%s/ESP/%s' % (
                        prefix, _ERS_element, node.hostname)
                    ESPsizeMB = os.stat(ESPpath).st_size >> 20

            if status['status'] in ('building', 'ready'):
                installpath = '%s/%s/untar/root' % (
                    BP.config['FILESYSTEM_IMAGES'], node.hostname)
                try:
                    with open(installpath + '/install.sh') as f:
                        installsh = f.read()
                    with open(installpath + '/install.log') as f:
                        installlog = f.read()
                except Exception as e:
                    installsh = installlog = None
                    pass

        # all manifests' names with namespace
        manifests = sorted(BP.blueprints['manifest'].get_all())
        return render_template(
            _ERS_element + '.tpl',
            label=__doc__,
            node=node,
            manifests=manifests,
            status=status,
            base_url=request.url.split(name)[0],
            ESPURL=ESPURL,
            ESPsizeMB=ESPsizeMB,
            installsh=installsh,
            installlog=installlog
        )
    except Exception as e:
        return make_response('Kaboom: %s' % str(e), 404)


@BP.route('/%s/ESP/<path:hostname>' % _ERS_element)
def web_node_send_ESP(hostname):
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
    response = jsonify({'nodes': list(BP.node_coords)})     # already sorted
    response.status_code = 200

    BP.logger.debug(response)
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
    else:
        response = jsonify({'mappings': nodes_info})
        response.status_code = 200
    BP.logger(response)
    return response


def _resolve_node_coord(nodespec):
    '''Discern whether the input is a number or a string, then
       lookup the node.
    param 'nodespec': node coordinate (usually w/o leading /) or an integer
    return: None or a qualified full node coordinate string
    '''
    node_coord = None
    try:
        node_id = int(nodespec)
        try:    # Sparseness holes return None which leads to AttributeError
            # FIXME: move into TMConfig and export a "node_id" property
            racknum = 1     # FRD/MFT
            encnum = ((node_id - 1) // 10) + 1
            nodenum = ((node_id - 1) % 10) + 1
            rack = BP.config['tmconfig'].racks[racknum]
            node_coord = rack.enclosures[encnum].nodes[nodenum].coordinate
        except (AttributeError, IndexError) as e:
            return None
    except ValueError:  # assume it's a coordinate path
        # Two rules invoke Postel's Law of liberal reception.  Either way,
        # we MAY need to add leading /.
        node_coord = nodespec if nodespec[0] == '/' else '/' + nodespec
    return node_coord if node_coord in BP.node_coords else None


@BP.route('/api/%s/<path:nodespec>' % _ERS_element, methods=('GET', ))
@BP.route('/api/%s//<path:nodespec>' % _ERS_element, methods=('GET', ))
def get_node_bind_info(nodespec=None):
    """
        List status json of the manifest bound to the node.
    """
    # Two rules invoke Postel's Law of liberal reception.  Either way,
    # we need to add leading /.
    node_coord = _resolve_node_coord(nodespec)
    if node_coord is None:
        response_msg = jsonify({ 'status' : 'No such node "%s"' % nodespec})
        response = make_response(response_msg,404)
        BP.logger.error(response)
        return response
    result = get_node_status(node_coord)
    if result is None:
        response_msg = jsonify({'status' : 'No Content'})
        response = make_response(response_msg, 204)
    else:
        response = make_response(jsonify(result), 200)
    BP.logger(response)
    return response


def node_coord2image_dir(node_coord):
    '''Calculate TFTP directory for kernel/FS from node coordinate/'''
    node_image_dir = BP.config['TFTP_IMAGES'] + '/' + \
        BP.nodes[node_coord][0].hostname
    assert os.path.isdir(node_image_dir), \
        'Missing directory "%s"' % node_image_dir
    return node_image_dir


@BP.route('/api/%s/<path:nodespec>' % _ERS_element, methods=('DELETE', ))
@BP.route('/api/%s//<path:nodespec>' % _ERS_element, methods=('DELETE', ))
def delete_node_binding(nodespec):
    """
        Remove Node to Manifest binding. Find node's folder in the TFTP
    directory by its hostname and clean out the content. Thus the next
    reboot will fail.

    :param 'nodespec': full node's coordinate to unbind Manifest from.
    """
    # Two rules invoke Postel's Law of liberal reception.  Either way,
    # we need to add leading /.
    node_coord = _resolve_node_coord(nodespec)
    if node_coord is None:
        response_msg = jsonify({'status' : 'No such node "%s"' % nodespec})
        response = make_response(response_msg, 404)
        BP.logger(response)    # chooses log level based on status code
        return response

    node_status = get_node_status(node_coord)
    if node_status and node_status['status'] == 'building':
        response_msg = jsonify({'status' : 'Cant delete binding - node is busy.'})
        return make_response(response_msg, 409)

    response_msg = jsonify({'status' : 'Successful cleanup.'})
    response = make_response(response_msg, 204)

    try:
        node_image_dir = node_coord2image_dir(node_coord)
        for node_file in glob(node_image_dir + '/*'):
            os.remove(node_file)
    except AssertionError as e:     # no such dir, no such binding
        pass
    except OSError as err:
        response_msg = jsonify({'status' : 'Failed to delete binding: %s' % err})
        response = make_response(response_msg, 500)
    BP.logger(response)    # chooses log level based on status code
    return response

####################### API (PUT) ###############################


@BP.route('/api/%s/<path:nodespec>' % _ERS_element, methods=('PUT', ))
@BP.route('/api/%s//<path:nodespec>' % _ERS_element, methods=('PUT', ))
def bind_node_to_manifest(nodespec=None):
    """
        Generate a custom filesystem image for a provided node coordinate
    using a manifest specified in the request's body. The resulting FS image
    will be placed at appropriate place under the TFTP hierarchy based on
    hostname.

    :param 'node_coord': absolute machine coordinate of the node
    """
    node_coord = _resolve_node_coord(nodespec)
    try:
        BP.logger.info('Binding manifest to a node [%s].' % (node_coord))

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
        manifest.validate_packages_tasks()
        response = build_node(manifest, node_coord)
    except BadRequest as e:
        response_msg = jsonify({'status' : e.get_response()})
        response = make_response(response_msg, resp_status)
    except (AssertionError, ValueError) as err:
        response_msg = jsonify({'status' : str(err)})
        response = make_response(response_msg, resp_status)
    BP.logger(response)
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
        response_msg = jsonify({'status' : 'Missing "Golden Image"!' })
        return make_response(response_msg, 505)

    # Each node gets its own set of dirs.  'nodes[]' matches snippets.
    hostname = BP.nodes[node_coord][0].hostname
    node_id = BP.nodes[node_coord][0].node_id
    sys_imgs = BP.config['FILESYSTEM_IMAGES']
    build_dir = os.path.join(sys_imgs, hostname)
    tftp_dir = BP.config['TFTP_IMAGES'] + '/' + hostname

    packages = manifest.thedict['packages']
    if packages:
        packages = ' '.join(packages)
    else:
        packages = None     # sentinel for following loop
    tasks = manifest.thedict['tasks']
    if tasks:
        tasks = ','.join(tasks)
    else:
        tasks = None     # sentinel for following loop

    DhcpClientId = BP.config['tmconfig'].allNodes[node_coord][0].DhcpClientId

    # Optional manifest fields not in the ERS but useful during bringup
    l4tm_privkey = manifest.thedict.get('l4tm_privkey', None)
    l4tm_pubkey = manifest.thedict.get('l4tm_pubkey', None)
    postinst = manifest.thedict.get('postinst', None)
    rclocal = manifest.thedict.get('rclocal', None)

    build_args = {
        'hostname':     hostname,
        'node_coord':   node_coord,
        'DhcpClientId': DhcpClientId,
        'node_id':      node_id,
        'manifest':     manifest,
        'tmconfig':     BP.config['TMCONFIG'],      # the file name
        'repo_mirror':  BP.config['L4TM_MIRROR'],
        'repo_release': BP.config['L4TM_RELEASE'],
        'repo_areas':   BP.config['L4TM_AREAS'],
        'packages':     packages,
        'tasks':        tasks,
        'l4tm_privkey': l4tm_privkey,
        'l4tm_pubkey':  l4tm_pubkey,
        'postinst':     postinst,
        'rclocal':      rclocal,
        'golden_tar':   golden_tar,
        'build_dir':    build_dir,
        'tftp_dir':     tftp_dir,
        'status_file':  tftp_dir + '/status.json',
        'verbose':      BP.VERBOSE,
        'debug':        BP.DEBUG,
        'logger':       BP.logger   # will get replaced in execute()
    }
    # Legacy technique called this as a subprocess.  Construct the command
    # for verbose output and manual invocation for development.
    cmd_args = []
    for key, val in build_args.items():
        if val is not None:     # packages and tasks, default is None
            cmd_args.append('--%s %s' % (key, val))
    cmd = os.path.dirname(__file__) + \
        '/node_builder/customize_node.py ' + ' '.join(cmd_args)

    response_msg = jsonify({'status' : '%s manifest set; image build initiated.' % hostname})
    response = make_response(response_msg, 201)

    if glob(tftp_dir + '/*.cpio'):
        response_msg = jsonify({'status' : 'Existing manifest changed; image re-build initiated.'})
        response = make_response(response_msg, 200)

    build_args = Namespace(**build_args)    # mutable

    # ------------------------- DRY RUN
    if BP.config['DRYRUN']:
        response.set_data(response.get_data().decode() + ' (DRY RUN)')
        print(cmd)      # Now you can cut/paste and run it by hand.
        customize_node.update_status(
            build_args, 'Node was built with a Dry Run.', status='ready')
        return response
    # ---------------------------------

    try:
        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(tftp_dir, exist_ok=True)
    except (EnvironmentError):
        response_msg = jsonify({'status' : 'Failed to create "%s"!' % build_dir })
        return make_response(response_msg, 505)

    # Before the child, to eliminate race condition if returning from
    # here to web-based actions.
    customize_node.update_status(
        build_args, 'Preparing to build PXE images.', status='building')

    if BP.DEBUG:
        set_trace()
        customize_node.execute(build_args)      # SHOULD return
        return response

    try:
        forked = os.fork()
    except OSError as err:
        response_msg = jsonify({'status' : 'AYE! Rocky\'s rookie got shot in the toe nail! [%s]' % err})
        return make_response(response_msg, 505)

    if forked > 0:  # wait for the child1 to exit.
        try:
            pid, retval = os.waitpid(forked, 0)
            if retval:
                response.status_code = 500
        except OSError as e:
            response.status_code = 500
        return response

    # The child makes a grandchild to build the node.  Close the flask socket.
    # Yes there's a window on multiple requestors, but I'm not ready for
    # eventlets yet.
    for i in range(3, 20):
        try:
            os.close(i)
        except OSError as err:
            if err.errno != errno.EBADF:
                BP.logger.warning('Could not close(%d): %s' % (i, str(err)))

    customize_node.execute(build_args)      # should NOT return
    BP.logger.critical('Unexpected return to child1')
    raise SystemExit('Unexpected return to child1')

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
    except (FileNotFoundError) as err:    # Unbound
        BP.logger.debug('<get_node_status> for %s: unbound' % (node_coord))
        return None
    except (AssertionError) as err:
        BP.logger.error('%s: %s' % (node_coord, str(err)))
        return None
    except Exception as err:       # TCNH =)
        status = {
            'message':  'Failed to parse status file: %s ' % str(err),
            'manifest': 'unknown',
            'status':   'error'
        }
    BP.logger.debug('<get_node_status> for %s: %s' % (
        node_coord, json.dumps(status, indent=4)))
    return status


def _load_data():
    """
        Scan tftp/images folder for known hostnames and read its status.json
    file. Save this data into a dictionary and return it to the user.

    :return: [dict] node_coordinate - node_status key value pair of the
        current status of the nodes.
    """
    global _data
    _data = {}
    for node in BP.nodes:
        node_status = get_node_status(node.coordinate)
        if node_status:
            _data[node.coordinate] = node_status
    return _data


def _manifest_lookup(name):
    # blueprints lookup has to be deferred until all are registered
    if name:
        name = name.strip('/')
    return BP.blueprints['manifest'].lookup(name)

###########################################################################


def register(url_prefix):
    BP.nodes = BP.config['tmconfig'].allNodes
    BP.node_coords = list([node.coordinate for node in BP.nodes])  # ordered
    BP.manifest_lookup = _manifest_lookup
    BP.mainapp.register_blueprint(BP, url_prefix=url_prefix)
    _load_data()
