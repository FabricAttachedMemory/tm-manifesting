#!/usr/bin/python3
"""TM Manifests
 This blueprint handles "manifest" related routines to allow users to upload
manifests, delete, list and download. Uploaded manifest are validated to be a
valid json string with required fields and will terminate if manifest is invalid.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"

import flask
import json
import os
from pdb import set_trace
import sys
import werkzeug

from tmms.utils import manifest_cfg

_ERS_element = 'manifest'

# See the README in the main templates directory.
BP = flask.Blueprint(_ERS_element, __name__)

###########################################################################

_UPFROM = 'uploaded_from'

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


def render_all(okmsg='', errmsg=''):
    return flask.render_template(
        _ERS_element + '_all.tpl',
        errmsg=errmsg,
        label=__doc__,
        keys=sorted(_data.keys()),
        okmsg=okmsg,
        base_url=flask.request.url)


@BP.route('/%s/' % _ERS_element)
@BP.route('/%s/<path:name>' % _ERS_element)
def webpage(name=None):

    if name is None:
        return render_all()     # Is this still showing "key"?

    if name not in _data:
        return flask.render_template(
            _ERS_element + '_all.tpl',
            label=__doc__,
            keys=sorted(_data.keys()),
            base_url=flask.request.url.split(name)[0])

    this = _data[name]
    return flask.render_template(
        _ERS_element + '.tpl',
        label=__doc__,
        name=name,
        itemdict=this.thedict,
        base_url=flask.request.url,
        data=this,
        rawtext=this.raw)


@BP.route('/%s/' % _ERS_element, methods=('POST', ))
def webpage_upload():
    try:
        assert int(flask.request.content_length) < 20000, 'Too big'
        file = flask.request.files['file[]']

        # fname = secure_filename(file.filename)
        # extension = os.path.splitext(file.filename)[1]
        # fname = str(uuid.uuid4()) + extension
        # file is a mixin, save() is a werkzeug method which calls
        # generic builtin open() and copies file.stream()
        # file.save(os.path.join(BP.UPLOADS, fname))
        contentstr = file.read().decode()
        m = manifest_cfg.ManifestDestiny('', '', BP, contentstr)
        msg = m.response.data.decode()
        _load_data()
        return render_all(okmsg=msg + ': ' + file.filename)

    except Exception as e:
        return render_all(errmsg='Upload("%s") failed: %s' % (
            file.filename, str(e)))

    _load_data()
    return render_all(okmsg='Upload %s complete' % file.filename)


###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths

@BP.route('/api/%s/' % _ERS_element)
def listall():
    """
        GET request that returns a JSON response of all the manifests
    uploaded to the server.
    """
    all_manifests = sorted(list(_data.keys()))
    msg = json.dumps({'manifests': all_manifests}, indent=4)
    status_code = 200
    if not all_manifests:
        status_code = 204
    response = flask.make_response(msg, status_code)
    BP.logger(response)    # level based on response status code
    return response


# @BP.route('/api/%s/' % _ERS_element) MAKES DUPLICATE RULE???  unittests pass
@BP.route('/api/%s/<path:manname>' % _ERS_element)
def show_manifest_json(manname='/'):
    """
        Find a specific manifest with respect to <prefix> and a <manifest name>
    and return a manifest contents in the response body.

    :param <prefix>: [str] full path to a user's manifesting folder.
    :return: json string with the full contents of the manifest,
            404 status code if manifest was not found.
    """
    response = None
    if manname.endswith('/'):
        response = list_manifests_by_prefix(manname.lstrip('/'))
    else:
        found_manifest = _lookup(manname)

        response = None
        if not found_manifest:
            response = flask.make_response(
                'The specified manifest does not exist.', 404)
        else:
            response = flask.make_response(flask.jsonify(found_manifest.thedict), 200)

    BP.logger(response)    # level based on response status code
    return response


def list_manifests_by_prefix(prefix=None):
    """
        This function loops throw _data.items() and for each element in it,
    finds match with the provided <prefix>. Note: the comparison is happening
    between _data's known manifests and provided <prefix> with a .startswith()
    function.

    :param <prefix>: [str] full path to user's manifesting folder e.g.
        "funutarama/" or "my/futurama/manifests/"

    :return: json string of { 'manifests' : ['prefix/manifest_name']
        Example: if there is a "futurama/" folder on the server that has
        'bender' and 'fry' manifests, then request to ../manifest/futurama/
        will result a response of
        "{ 'manifests' : ['futurama/bender', 'futurama/fry'] }".
    """
    result = {'manifests': []}

    for man_path, man_obj in _data.items():
        if man_path.startswith(prefix) or not prefix:
            result['manifests'].append(man_path)

    if not result['manifests']:
        response = flask.make_response('No Manifests are available.', 204)
    else:
        response = flask.make_response(jsonify(result), 200)

    BP.logger(response)    # level based on status code
    return response

# Must have a string greater or equal to 1. Thats the RULE for Flask's rules
# (<path:str>).  Reference: http://werkzeug.pocoo.org/docs/0.11/routing/
# Thus, to upload to root folder, we have to have a separate rule.


@BP.route('/api/%s/' % _ERS_element, methods=(('POST', )))  # Upload to Root
@BP.route('/api/%s/<path:prefix>' % _ERS_element, methods=(('POST', )))
def api_upload(prefix=''):
    """
        Upload a manifest to the server using json string body content provided
    in the Request.

    :param 'prefix': (optional) namespace path for the manifest to upload to.
                    e.g: when prefix = futurama/world/, manifest will be
                    uploaded into that provided folder on the server.
                    when prefix = '' then manifest will be uploaded into
                    base of the server's manifest uploads location.
    """
    if prefix and not prefix.endswith('/'):    # FIXME WHY IS THIS BAD?
        flask.abort(404)
    try:
        assert int(flask.request.headers['Content-Length']) < 20000, 'Too big'
        contentstr = flask.request.get_data().decode()

        if BP.config['DRYRUN']:
            _data[prefix] = 'dry-run'
            BP.logger(response)    # level based on status cod3
            return response
        else:
            manifest = manifest_cfg.ManifestDestiny(prefix, '', BP, contentstr)
        response = manifest.response

    except Exception as e:
        response = flask.make_response('Manifest upload failed: %s' % str(e), 422)

    BP.logger(response)    # level based on status code
    _load_data()
    return response


@BP.route('/api/%s/<path:manname>' % _ERS_element, methods=(('DELETE', )))
def delete_manifest(manname=None):
    """
        Deletes an existing manifest from the service. Note that this simply
    deletes the manifest itself and that any nodes configured to use the
    manifest will continue to boot using the existing kernel and file system.

    :param 'prefix': manifest path used to create PUT manifest to a server
    :param 'manname': manifest file name
    """
    found_manifest = _lookup(manname)
    response = flask.make_response('The specified manifest has been deleted.', 204)

    if not found_manifest:
        response = flask.make_response('The specified manifest does not exist.', 404)
    else:
        manifest_server_path = BP.config['MANIFEST_UPLOADS'] + '/' + manname

        try:
            if not BP.config['DRYRUN']:
                os.remove(manifest_server_path)
                # TODO: remove prefix folders of the manifests if empty
        except EnvironmentError as err:
            response = flask.make_response('Failed to remove manifest', 500)

    BP.logger(response)    # level based on status code
    _load_data()
    return response


###########################################################################


def _lookup(manifest_name):    # Can be sub/path/name
    manifest_name = manifest_name.strip('/')
    return _data.get(manifest_name, None)


def get_all():
    return tuple(_data.keys())


def is_file_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in BP.allowed_files

###########################################################################

_data = None


def _load_data():
    global _data
    _data = {}
    manfiles = [    # List comprehension
        (dirpath, f) for dirpath, dirnames, fnames in os.walk(BP.UPLOADS)
        for f in fnames
    ]
    for dirpath, basename in manfiles:
        try:
            this = manifest_cfg.ManifestDestiny(dirpath, basename, BP)

            # Start with a full path, then a relative part, then the namespace
            manname = os.path.join(dirpath, basename)   # Build a full path
            manname = manname.split(BP.config['MANIFEST_UPLOADS'])[-1]
            # folder. e.g. user_folder/my_manifest
            manname = os.path.normpath(manname).strip('/')

            # search is expected by manifest name, (e.g. manifest.json, not
            # path/manifest.json)
            _data[manname] = this
        except Exception as e:
            pass


def register(url_prefix):
    BP.lookup = _lookup
    BP.get_all = get_all
    BP.UPLOADS = BP.config['MANIFEST_UPLOADS']
    BP.mainapp.register_blueprint(BP, url_prefix=url_prefix)
    _load_data()
