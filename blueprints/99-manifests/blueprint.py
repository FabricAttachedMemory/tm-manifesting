'''TM Manifests'''
import json
import os
import sys
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify, g
from werkzeug import secure_filename

_ERS_element = 'manifest'

# See the README in the main templates directory.
BP = Blueprint(_ERS_element, __name__)

###########################################################################


_UPFROM = 'uploaded_from'


@BP.before_request
def before_reques():
    """
        Update _data variable before each request so that it's values are in sync
    with the server's manifest files.
    """
    _load_data()


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
        url_base=request.url)


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
        assert int(request['Content-Length']) < 20000, 'Too big'
        file = request.files['file[]']

        # fname = secure_filename(file.filename)
        # extension = os.path.splitext(file.filename)[1]
        # fname = str(uuid.uuid4()) + extension
        # file is a mixin, save() is a werkzeug method which calls
        # generic builtin open() and copies file.stream()
        # file.save(os.path.join(BP.UPLOADS, fname))
        contentstr = file.read().decode()
        m = ManifestDestiny('', '', contentstr)
        msg = 'Overwrote' if  m.key in _data else 'Uploaded'    # before...
        load_data()
        return render_all(okmsg=msg + ' ' + file.filename)

    except Exception as e:
        return render_all(errmsg='Upload("%s") failed: %s' %
            (file.filename, str(e)))

    _load_data()
    return render_all(okmsg='Upload %s complete' % file.filename)


###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths

@BP.route('/api/%s/' % _ERS_element)
def listall():
    """
        GET request that returns a json string response of all the manifests uploaded
    to the server.
    """
    response = jsonify({ 'manifests' : sorted(list(_data.keys())) })
    response.status_code = 200
    return response


@BP.route('/api/%s/<path:prefix>/' % _ERS_element)
def manifests_by_prefix(prefix=None):
    """
        This function loops throw _data.items() and for each element in it, finds
    match with the provided <prefix>. Note: the comparison is happening between
    _data's known manifests and provided <prefix> with a .startswith() function.

    :param <prefix>: [str] full path to user's manifesting folder e.g. "funutarama/" or "my/futurama/manifests/"

    :return: json string of { 'manifests' : ['prefix/manifest_name']
                Example: if there is a "futurama/" folder on the server that has
                'bender' and 'fry' manifests, then request to ../manifest/futurama/
                will reesult a respons of "{ 'manifests' : ['futurama/bender', 'futurama/fry'] }".
    """
    result = { 'manifests' : [] }

    for known_prefix, man_obj in _data.items():
        prefix = os.path.normpath(prefix)
        if known_prefix.startswith(prefix):
            man_output = os.path.join(prefix, man_obj.basename)
            result['manifests'].append(man_output)

    if not result['manifests']:
        response = jsonify({ 'No Content' :         # FIXME: this message string is ignored for 204 status code
                            'No Manifests are available under the provided path.'})
        response.status_code = 204
    else:
        response = jsonify(result)
        response.status_code = 200

    return response


@BP.route('/api/%s/<path:prefix>/<path:manname>' % _ERS_element)
def show_manifest_json(prefix=None, manname=None):
    """
        Find a specifiec manifest with respect to <prefix> and a <manifest name>.

    :param <prefix>: [str] full path to a user's manifesting folder.
    :return: json string with the full contents of the manifest,
            404 status code if manifest was not found.
    """
    prefix_manname = prefix + '/' + manname

    found_manifest = _lookup(prefix_manname)

    if not found_manifest:
        response = jsonify({'Not Found' :
                            'The specified manifest does not exist.' })
        response.status_code = 404
        return response

    manifest_result = found_manifest.thedict
    response = jsonify(manifest_result)
    response.status_code = 200

    return response


@BP.route('/api/%s/<path:manname>/' % _ERS_element, methods=(('PUT', )))
def api_upload(manname=None):
    manname = manname.rstrip('/')
    response = jsonify({ 'success' : 'A new manifest has been created with the provided contetnts!' })
    response.status_code = 201  # but not always

    if os.path.exists(BP.UPLOADS + '/' + manname):
        response = jsonify({ 'warning' :
            'An existed manifest "%s" has been replaced with new contents.' % manname })
        response.status_code = 200

    try:
        assert int(request.headers['Content-Length']) < 20000, 'Too big'
        contentstr = request.get_data().decode()
        if BP.config['DRYRUN']:
            _data[manname] = 'dry-run'
            return response
        else:
            ManifestDestiny(manname, '', contentstr)
    except Exception as e:
        response = jsonify({ 'error': 'Couldn\'t upload manifest! %s' % str(e) })
        response.status_code = 422

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
        legal = frozenset(
            ('name', 'description', 'release', 'tasks', 'packages')
        )
        keys = frozenset(m.keys())
        missing = list(legal - keys)
        assert not len(missing), 'Missing key(s): ' + ', '.join(missing)
        molegal = legal.union(frozenset(('comment', '_comment')))
        illegal = list(keys - molegal - frozenset((_UPFROM, )))
        assert not len(illegal), 'Illegal key(s): ' + ', '.join(illegal)
        assert m['tasks'] or m['packages'], 'empty manifest'

        nosuch = BP.mainapp.blueprints['package'].filter(m['packages'])
        assert not nosuch, 'no such package(s) ' + ', '.join(nosuch)

        nosuch = BP.mainapp.blueprints['task'].filter(m['tasks'])
        assert not nosuch, 'no such task(s) ' + ', '.join(nosuch)

        return m


    def __init__(self, dirpath, basename, contentstr=None):
        '''If contentstr is given, it is an upload, else read a file.'''
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
            os.makedirs(self.dirpath, exist_ok=True)
            with open(os.path.join(self.dirpath, fname), 'w') as f:
                f.write(contentstr)
            return

        assert '/' not in basename, 'basename is not a leaf element'
        fname = os.path.join(dirpath, basename)

        with open(fname, 'r') as f:
            self.raw = f.read()

        self.thedict = self.validate_manifest(self.raw)
        self.dirpath = dirpath
        self.basename = basename


    @property
    def fullpath(self):
        return '%s/%s' % (self.dirpath, self.basename)

    @property
    def namespace(self):
        if self.dirpath.startswith(BP.UPLOADS):
            tmp = self.dirpath.split(BP.UPLOADS)[-1][1:]    # chomp leading /
            return tmp
        # Some kind of relative path, just send it all back
        tmp = os.path.join(self.dirpath.split(self.basename)[0])
        return tmp

    @property
    def key(self):
        return os.path.join(self.namespace, self.basename)

###########################################################################

def _lookup(manifest_name):    # Can be sub/path/name
    return _data.get(manifest_name, None)


def is_file_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in BP.allowed_files

###########################################################################

_data = None


def _load_data():
    global _data
    _data = { }
    try:    # don't die in a daemon
        manfiles = [    # List comprehension
            (dirpath, b)
                for dirpath, dirnames, basenames in os.walk(BP.UPLOADS)
                    for b in basenames
        ]
        for dirpath, basename in manfiles:
            this = ManifestDestiny(dirpath, basename)

            manname = os.path.join(dirpath, basename)                   # Build a manifest full path
            manname = manname.split(BP.config['MANIFEST_UPLOADS'])[-1]  # relative to Manifest Uploads
            manname = os.path.normpath(manname).strip('/')              # folder. e.g. user_folder/my_manifest

            _data[manname] = this # search is expected by manifest name, (e.g. manifest.json, not path/manifest.json)
    except Exception as e:
        pass


def register(mainapp):  # take what you like and leave the rest
    BP.mainapp = mainapp
    BP.config = mainapp.config
    BP.lookup = _lookup
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    BP.UPLOADS = BP.config['MANIFEST_UPLOADS']
    _load_data()
