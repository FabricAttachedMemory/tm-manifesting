'''TM Nodes'''

from collections import namedtuple
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
    if len(_data) == 0:
        response = jsonify( { 'No Content' : 'There are no manifests associated with any nodes.' } )
        response.status_code = 204
        return response

    nodes_info = {}
    for node_coord, manname in _data.items():
        nodes_info[node_coord] = {}

        nodes_info[node_coord]['manifest'] = manname
        if node_coord in BP.node_status:
            nodes_info[node_coord]['status'] = BP.node_status[node_coord].poll()
        else:
            nodes_info[node_coord]['status'] = 'Unknown'
        nodes_info[node_coord]['message'] = 'Life is good.'

    response = jsonify( { 'mappings' : nodes_info } )
    response.status_code = 200
    return response


@BP.route('/api/%s/<path:node_coord>' % _ERS_element, methods=('GET', ))
def get_node_bind_info(node_coord=None):
    """
        List status json of the manifest binded to the node.
    """
    if node_coord not in BP.node_coords:
        return make_response('The specified node does not exist.' ,404)

    manname = _data.get(node_coord, None).lstrip('/')

    manifest = BP.manifest_lookup(manname)
    if not manifest:
        return make_response('There is no manifest associated with the specified node.', 204)

    result = node_status(node_coord)

    return make_response(jsonify(result), 200)


def node_status(node_coord):
    nbind = NodeBinding.process(node_coord)

    result = {}
    result['manifest'] = nbind.manname
    result['status'] = nbind.status

    if result['status'] == 'error':
        result['message'] = nbind.error
    elif result['status'] == 'building':
        result['message'] = 'Binding to the Node is in progress'
    else:
        result['message'] = 'Finished without errors.'

    return result

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

        response = build_node(manifest, node_coord)
    except BadRequest as e:
        response = make_response(e.get_response(), 500)
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

    build_args = {}
    build_args['fs-image'] = custom_tar
    build_args['hostname'] = node_hostname
    build_args['tftp'] = tftp_node_dir
    build_args['verbose'] = BP.VERBOSE
    build_args['debug'] = BP.DEBUG
    build_args['packages'] = manifest.thedict['packages']

    cmd_args = []
    for key, val in build_args.items():
        cmd_args.append('--%s %s' % (key, val))
    cmd = os.path.dirname(__file__) + '/node_builder/customize_node.py ' + ' '.join(cmd_args)
    cmd = shlex.split(cmd)

    _ = NodeBinding(node_coord, os.path.join(manifest.prefix, manifest.basename).lstrip('/'), cmd)
    #process = subprocess.Popen(cmd, stderr=subprocess.PIPE)

    #BP.node_status[node_coord] = namedtuple('NodeProcess', 'process status err')
    #BP.node_status[node_coord].process = process

    #if status['status'] >= 500:
    #    response = make_response(status['message'], status['status'])

    return response

###########################################################################

class NodeBinding(object):

    _binding = {}       # { noode_coord : NodeBinding class }
                        # Stores all the node binding requests.

    def __init__(self, coord, manname, cmd):
        self.coord = coord
        self.manname = manname
        self._cmd = cmd         # save cmd for debugging
        self.error = None
        self.returncode = None

        if coord in self._binding:
            if self.status == 'busy':
                raise RuntimeError('Node is busy!')

        self._popen = subprocess.Popen(self._cmd, stderr=subprocess.PIPE)
        self._binding[self.coord] = self


    @classmethod
    def process(cls, coord):
        node_binding = cls._binding.get(coord, None)
        if node_binding is None:
            return None
        else:
            return node_binding


    @property
    def status(self):
        """
        :return: False - No process has been lauched for a node.
                'error' - There was an error during the Node building (observe
                        self.error for an error message)
                'building' - Node is busy waiting for a custom filesystem image.
                'ready' - Node is ready to boot. No process is running.
        """
        if self.error:
            return 'error'
        if self.process(self.coord) is None:
            return False

        poll_status = self.process(self.coord)._popen.poll()
        if poll_status is None:
            return 'building'
        elif(poll_status != 0):
            _, err = self._binding[self.coord]._popen.communicate()
            self.returncode = poll_status               # Save returncode for debugging.
            self.error = err.decode().split('\n')[-2]   # get exception message TODO: better parsing
            return 'error'

        return 'ready'

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
    BP.node_status = {}
    BP.blueprints = mainapp.blueprints
    BP.manifest_lookup = _manifest_lookup
    BP.binding = BP.config['NODE_BINDING'] # json file of all the Node to Manifest bindings.
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _load_data()
