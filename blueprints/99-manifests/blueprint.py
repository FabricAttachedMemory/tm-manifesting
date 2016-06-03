'''TM Manifests'''
import json
import os
import re
import sys
from shutil import copyfile
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

    _load_data()
    return render_all(okmsg='Upload %s complete' % file.filename)


###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths
@BP.route('/api/%s/<manname>' % _ERS_element, methods=('DELETE',))
def deletemanifest(manname=None):
    """
        Deletes an existing manifest from the service. Note that this simply deletes the
    manifest itself and that any nodes configured to use the manifest will continue to
    boot using the constructed kernel and root file system.
    """
    _load_data()
    if not manname.endswith('.json'):
        manname = manname + '.json'
    manifest = BP.lookup(manname)
    if not manifest:
        response = jsonify( {'error' : 'Manifest "%s" was not found!' % manname} )
        response.status_code = 404
        return response

    if not delete_manifest(manname):
        response = jsonify ( {'error' : 'Error occured while removing "%s"!' % manname } )
        response.status_code = 500
        return response

    response = jsonify({'success' : 'Manifest "%s" was removed!' % manname })
    response.status_code = 200
    return response


@BP.route('/api/%s/' % _ERS_element)
def listall():
    """
        GET request that returns a json string response of all the manifests uploaded
    to the server.
    """
    _load_data()
    all_manifests = { 'manifest' : [], 'directory' : [] }
    for manname, man_obj in _data.items():
        all_manifests['manifest'].append(manname)
        all_manifests['directory'].append(man_obj.dirpath)

    response = jsonify(all_manifests)
    response.status_code = 200
    return response


@BP.route('/api/%s/<path:name>/' % _ERS_element)
def api(name=None):
    response = jsonify({ 'error': 'API GET not implemented' })
    response.status_code = 501
    return response


@BP.route('/api/%s/<path:manname>/' % _ERS_element, methods=(('PUT', )))
def api_upload(manname=None):
    _load_data()
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
        ManifestDestiny(manname, '', contentstr, dry_run=BP.config['DRYRUN'])
    except Exception as e:
        response = jsonify({ 'error': 'Couldn\'t upload manifest! %s' % str(e) })
        response.status_code = 422

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


    def __init__(self, dirpath, basename, contentstr=None, **kwargs):
        '''If contentstr is given, it is an upload, else read a file.'''
        self._dry_run = kwargs.get('dry_run', False)

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

            if self._dry_run:
                print('Dry run: skipping manifest creation.')       # keep 'print', until Log to file is implemented
                return

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


def delete_manifest(manname):
    """
        Move an existed uploaded manifest into a trashbin.

    :param 'manname': [str] manifest to delete (move to trashbin)
    :return: True - on success. False - on fail.
    """
    trashbin = BP.config['MANIFESTING_ROOT'] + '/trashbin/'
    cp_from = BP.config['MANIFEST_UPLOADS'] + '/' + manname
    cp_into = trashbin + '/' + manname

    if not os.path.isdir(trashbin):
        os.makedirs(trashbin)

    while os.path.exists(cp_into):                  # increment file's copy index
        cp_into = increment_copy_name(cp_into)      # until a 'non existing copy in the folder' is found.

    try:
        copyfile(cp_from, cp_into)
        os.remove(BP.config['MANIFEST_UPLOADS'] + '/' + manname)
    except EnvironmentError as err:
        return False # Don't care about error. It failed doing "move" operating. That all I need.
    return True


def increment_copy_name(filename):
    """
        Add a '(number)' string to the end of filename. If pattern already in
    the string - increment 'number' and return a new filename with an incremented
    copy number, e.g. filename = manifest.json  ---> manifest.json(1)
                      filename = manifest.json(1) ---> manifest.json(2)
    """
    pttrn_found = re.search(r'\(\d+\)', filename)
    if pttrn_found is None:
        return filename + '(1)'

    if not filename.endswith(pttrn_found.group(0)):
        return filename + '(1)'

    curr_copy_index = re.search('\d+', pttrn_found.group(0)).group(0)
    new_copy_index = int(curr_copy_index) + 1
    return filename.replace(pttrn_found.group(0), '(%s)' % new_copy_index)


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
    BP.UPLOADS = BP.config['MANIFEST_UPLOADS']
    _load_data()
