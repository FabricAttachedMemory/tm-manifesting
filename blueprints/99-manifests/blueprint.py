#!/usr/bin/python3
'''TM Manifests'''
import json
import os
from glob import glob
import sys
from shutil import rmtree
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify
from flask import g, abort, make_response
from werkzeug import secure_filename

_ERS_element = 'manifest'

# See the README in the main templates directory.
BP = Blueprint(_ERS_element, __name__)

###########################################################################

_UPFROM = 'uploaded_from'

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


def render_all(okmsg='', errmsg=''):
    return render_template(
        _ERS_element + '_all.tpl',
        errmsg=errmsg,
        label=__doc__,
        keys=sorted(_data.keys()),
        okmsg=okmsg,
        base_url=request.url)


@BP.route('/%s/' % _ERS_element)
@BP.route('/%s/<path:name>' % _ERS_element)
def webpage(name=None):

    if name is None:
        return render_all()     # Is this still showing "key"?

    this = _data[name]
    return render_template(
        _ERS_element + '.tpl',
        label=__doc__,
        name=name,
        itemdict=this.thedict,  # FIXME: just pass "this"
        rawtext=this.raw)


@BP.route('/%s/' % _ERS_element, methods=('POST', ))
def webpage_upload():
    try:
        assert int(request.content_length) < 20000, 'Too big'
        file = request.files['file[]']

        # fname = secure_filename(file.filename)
        # extension = os.path.splitext(file.filename)[1]
        # fname = str(uuid.uuid4()) + extension
        # file is a mixin, save() is a werkzeug method which calls
        # generic builtin open() and copies file.stream()
        # file.save(os.path.join(BP.UPLOADS, fname))
        contentstr = file.read().decode()
        m = ManifestDestiny('', '', contentstr)
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
    response = make_response(msg, status_code)
    BP.logging(response)    # utils.logging.logger will handle logging Level
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
            response = make_response('The specified manifest does not exist.', 404)
        else:
            response = make_response(jsonify(found_manifest.thedict), 200)

    BP.logging(response)    # utils.logging.logger will handle logging Level
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
        response = make_response('No Manifests are available.', 204)
    else:
        response = make_response(jsonify(result), 200)

    BP.logging(response)    # utils.logging.logger will handle logging Level
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
        abort(404)
    try:
        assert int(request.headers['Content-Length']) < 20000, 'Too big'
        contentstr = request.get_data().decode()

        if BP.config['DRYRUN']:
            _data[prefix] = 'dry-run'
            BP.logging(response)    # utils.logging.logger will handle logging Level
            return response
        else:
            manifest = ManifestDestiny(prefix, '', contentstr)
        response = manifest.response

    except Exception as e:
        BP.logging.error('Manifest upload failed: %s' % (e))
        response = make_response('Upload failed: %s' % str(e), 422)

    BP.logging(response)    # utils.logging.logger will handle logging Level
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
    response = make_response('The specified manifest has been deleted.', 204)

    if not found_manifest:
        response = make_response('The specified manifest does not exist.', 404)
    else:
        manifest_server_path = BP.config['MANIFEST_UPLOADS'] + '/' + manname

        try:
            if not BP.config['DRYRUN']:
                os.remove(manifest_server_path)
                # TODO: cleanout prefix folders of the manifests if it is empty!
        except EnvironmentError as err:
            response = make_response('Failed to remove requested manifest!', 500)

    BP.logging(response)    # utils.logging.logger will handle logging Level
    _load_data()
    return response


###########################################################################


class ManifestDestiny(object):

    @staticmethod
    def validate_manifest(contentstr):
        '''Raise an error or return a dictionary representing a manifest.'''
        try:
            m = json.loads(contentstr)
        except Exception as e:
            raise RuntimeError('not JSON')
        legal = frozenset(  # Required
            ('name', 'description', 'release', 'tasks', 'packages')
        )
        keys = frozenset(m.keys())
        missing = list(legal - keys)
        assert not len(missing), 'Missing key(s): ' + ', '.join(missing)

        molegal = legal.union(frozenset(    # Optional
            ('comment', '_comment', 'l4tm_pubkey')))
        illegal = list(keys - molegal - frozenset((_UPFROM, )))
        assert not len(illegal), 'Illegal key(s): ' + ', '.join(illegal)

        return m

    def validate_packages_tasks(self):
        '''Defer until binding time'''
        man = self.thedict
        nosuch = BP.mainapp.blueprints['package'].filter(man['packages'])
        assert not nosuch, 'no such package(s): ' + ', '.join(nosuch)

        nosuch = BP.mainapp.blueprints['task'].filter(man['tasks'])
        assert not nosuch, 'no such task(s): ' + ', '.join(nosuch)

    def __init__(self, dirpath, basename, contentstr=None):
        '''If contentstr is given, it is an upload, else read a file.'''
        assert '/' not in basename, 'basename is not a leaf element'
        self.basename = basename
        # excludes basename, more like a namespace
        self.prefix = dirpath.split(BP.UPLOADS)[-1].strip('/')
        if contentstr is not None:
            # some kind of upload, basename not used
            self.thedict = self.validate_manifest(contentstr)
            self.raw = contentstr
            elems = dirpath.split(os.path.sep)

            assert len(elems) < 10, 'Really? %d deep? Get a life.' % len(elems)

            for e in elems:
                assert e == secure_filename(e), \
                    'Illegal namespace component "%s"' % e

            fname = secure_filename(self.thedict['name'])
            assert fname == self.thedict['name'], 'Illegal (file) name'

            self.dirpath = os.path.join(BP.UPLOADS, dirpath)
            self.manifest_file = BP.UPLOADS + '/' + self.namespace

            if os.path.exists(self.manifest_file):
                self.response = make_response(
                    'An existing manifest has been overwritten.', 200)
            else:
                self.response = make_response(
                    'A new manifest has been created.', 201)

            os.makedirs(self.dirpath, exist_ok=True)
            with open(self.manifest_file, 'w') as f:
                f.write(contentstr)
            return

        fname = os.path.join(dirpath, basename)

        with open(fname, 'r') as f:
            self.raw = f.read()

        self.thedict = self.validate_manifest(self.raw)
        self.dirpath = dirpath

    @property
    def fullpath(self):
        return '%s/%s' % (self.dirpath, self.basename)

    @property
    def namespace(self):
        namespace = self.prefix + '/' + self.thedict['name']
        namespace = os.path.normpath(namespace)
        namespace = namespace.strip('/')
        return namespace

    @property
    def key(self):  # FIXME returns trailing slash
        return os.path.join(self.namespace, self.basename)

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
            this = ManifestDestiny(dirpath, basename)

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
