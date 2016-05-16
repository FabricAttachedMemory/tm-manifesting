'''TM Manifests'''

import glob
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
    # files = request.files.getlist('file[]')
    # for file in files:
        # if not file: #
            # continue
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

    load_data()
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
    all_manifests = { 'manifest' : [] }
    for manfile in glob.glob(BP.UPLOADS + '/*'):
        all_manifests['manifest'].append(os.path.basename(manfile))
    response = jsonify(all_manifests)
    response.status_code = 200
    return response


@BP.route('/api/%s/' % _ERS_element)
@BP.route('/api/%s/<path:name>/' % _ERS_element)
def api(name=None):
    response = jsonify({ 'error': 'API GET not implemented' })
    response.status_code = 501
    return response


@BP.route('/api/%s/<path:manname>/' % _ERS_element, methods=(('PUT', )))
def api_upload(manname=None):
    manname = manname.rstrip('/')
    response = jsonify({ 'success' : 'A new manifest has been created with the provided contetnts!' })
    response.status_code = 201  # but not always
    if os.path.exists(BP.UPLOADS + '/' + manname + '.json'):
        response = jsonify({ 'warning' :
            'An existed manifest [%s] has been replaced with new contents.' % manname})
        response.status_code = 200

    try:
        assert int(request.headers['Content-Length']) < 20000, 'Too big'
        contentstr = request.files['manifest_file'].read().decode()
        contentstr = json.loads(contentstr)
        m = ManifestDestiny('', '', json.dumps(contentstr, indent=4))
    except Exception as e:
        response = jsonify({ 'error': 'Couldn\'t upload manifest! [%s]' % str(e) })
        response.status_code = 422
        return response

    return response


###########################################################################


class ManifestDestiny(object):

    from shutil import copyfile


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

            fname = secure_filename(self.thedict['name']).lower()   # Lowercase manifest name here!
            assert fname == self.thedict['name'].lower(), 'Illegal (file) name'  # validate as non-case sensitive
            self.dirpath = os.path.join(BP.UPLOADS, dirpath)
            os.makedirs(self.dirpath, exist_ok=True)
            manifest_file = os.path.join(self.dirpath, fname)

            if not manifest_file.endswith('.json'):
                manifest_file = manifest_file + '.json'

            self.create_file(manifest_file, contentstr)

            return

        assert '/' not in basename, 'basename is not a leaf element'
        fname = os.path.join(dirpath, basename)
        with open(fname, 'r') as f:
            self.raw = f.read()
        self.thedict = self.validate_manifest(self.raw)
        self.dirpath = dirpath
        self.basename = basename


    def create_file(self, target, content):
        """
            Create a file in the targeted location with a desiered content.
        If file exists - then it will be overwritten.
        :param 'target': [str] full path to a file to create (including a file name itself)
        :param 'content': [str] data for to put inside the new created file.
        :return: None. Or RuntimeError is raised on error.
        """
        backupfile = target + '.old'
        try:
            if os.path.exists(backupfile):
                copyfile(target, backupfile)
                os.remove(target)
        except EnvironmentError as err:
            raise RuntimeError('Couldn\'t backup file during manifest creation! [%s]' % err)

        with open(target, 'w') as f:
            f.write(content)

        try:
            if os.path.exists(backupfile):
                os.remove(backupfile)
        except EnvironmentError as err:
            raise RuntimeWarning('Couldn\'t remove a backup file during manifest creation! [%s]' % err)


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
            _data[basename] = this # search is expected by manifest name, (e.g. manifest.json, not path/manifest.json)
    except Exception as e:
        pass


def register(mainapp):  # take what you like and leave the rest
    BP.mainapp = mainapp
    BP.config = mainapp.config
    BP.lookup = _lookup
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    BP.UPLOADS = os.path.normpath(BP.config['MANIFESTING_ROOT'] + '/manifest_uploads/')
    _load_data()
