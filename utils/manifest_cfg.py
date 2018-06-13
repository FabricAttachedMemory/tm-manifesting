#!/usr/bin/python3
import os
import flask
import json
import werkzeug


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

        molegal = legal.union(frozenset((    # Optional
            'comment', '_comment', 'privkey', 'pubkey',
            'l4tm_privkey', 'l4tm_pubkey',              # Deprecated
            'postinst', 'rclocal', 'kernel_append')))

        #NO NEED TO BE STRICT ANYMORE
        #illegal = list(keys - molegal - frozenset((_UPFROM, )))
        #assert not len(illegal), 'Illegal key(s): ' + ', '.join(illegal)

        return m


    def validate_packages_tasks(self):
        '''Defer until binding time'''
        man = self.thedict
        nosuch = self.BP.mainapp.blueprints['package'].filter(man['packages'])
        #FIXME: Validate PACKAGE exist in mirror!
        assert not nosuch, 'no such package(s): ' + ', '.join(nosuch)

        nosuch = self.BP.mainapp.blueprints['task'].filter(man['tasks'])
        assert not nosuch, 'no such task(s): ' + ', '.join(nosuch)


    def __init__(self, dirpath, basename, BP, contentstr=None):
        '''If contentstr is given, it is an upload, else read a file.'''
        assert '/' not in basename, 'basename is not a leaf element'
        self.basename = basename
        self.BP = BP
        # excludes basename, more like a namespace
        self.prefix = dirpath.split(self.BP.UPLOADS)[-1].strip('/')
        if contentstr is not None:
            # some kind of upload, basename not used
            self.thedict = self.validate_manifest(contentstr)
            self.raw = contentstr
            elems = dirpath.split(os.path.sep)

            assert len(elems) < 10, 'Really? %d deep? Get a life.' % len(elems)

            for e in elems:
                assert e == werkzeug.secure_filename(e), \
                    'Illegal namespace component "%s"' % e

            fname = werkzeug.secure_filename(self.thedict['name'])
            assert fname == self.thedict['name'], 'Illegal (file) name'

            self.dirpath = os.path.join(self.BP.UPLOADS, dirpath)
            self.manifest_file = self.BP.UPLOADS + '/' + self.namespace

            if os.path.exists(self.manifest_file):
                self.response = flask.make_response(
                    'An existing manifest has been overwritten.', 200)
            else:
                self.response = flask.make_response(
                    'A new manifest has been created.', 201)

            os.makedirs(self.dirpath, exist_ok=True)
            #Json format the content for better readability
            formatted_content = json.dumps(self.thedict, indent=4, sort_keys=True)
            #Save manifest content into server destination ([...]tmms/manifest/)
            with open(self.manifest_file, 'w') as f:
                f.write(formatted_content)
            return

        fname = os.path.join(dirpath, basename)

        with open(fname, 'r') as f:
            self.raw = f.read()

        self.thedict = self.validate_manifest(self.raw)
        self.dirpath = dirpath


    def get(self, key, default_value=None):
        ''' Return value of the 'key' from self.thedict. None if key not found. '''
        return self.thedict.get(key, default_value)


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
