#!/usr/bin/python3
"""L4TM packages
 This blueprint handles "packages" routines to allow users to list packages and
its metadata based of the manifesting-server api Mirror value.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


from collections import defaultdict
from flask import Blueprint, render_template, request, jsonify, make_response
import gzip
import logging
import os
import requests as HTTP_REQUESTS
import sys

from debian.deb822 import Packages
from io import BytesIO, StringIO
from pdb import set_trace

from tmms.utils import utils

_ERS_element = 'package'

# See the README in the main templates directory.
BP = Blueprint(_ERS_element, __name__)

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/%ss/' % _ERS_element)       # Plurar form of the element name to list all Packages
@BP.route('/%s/<name>' % _ERS_element)  # Songular - to list one package.
def _webpage(name=None):
    if _data is None:
        _load_data()

    if name is None:    # overloaded detection of singular rule
        return render_template(
            _ERS_element + '_all.tpl',
            label=__doc__,
            keys=sorted(_data.keys()),
            alphabetic_sets=alphabetic_sets(_data.keys()),
            base_url=request.url)

    return render_template(
        _ERS_element + '.tpl',
        label=__doc__,
        name=name,
        base_url=request.url,
        itemdict=_data[name])


def alphabetic_sets(data):
    result = defaultdict(list)
    for val in data:
        if val[0].isalpha():
            result[val[0]].append(val)
        else:
            result['_digit'].append(val)
    return result

###########################################################################
# API
# As a blueprint registration against mainapp, these are relative paths


@BP.route('/api/%ss/' % _ERS_element)       # Plurar form of the element name to list all Packages
@BP.route('/api/%s/<name>' % _ERS_element)  # Songular - to list one package.
def _api(name=None):
    if _data is None:
        _load_data()

    status_code = 200
    if name is None:
        packages = [ ]
        for pkg in _data.values():
            tmpdict = {
                'package': pkg['Package'],
                'version': pkg['Version'],
                'description': pkg['Description']
            }
            packages.append(tmpdict)

        if not packages:
            status_code = 204

        return make_response(jsonify({ 'package': packages }), status_code)

    pkg = _data.get(name, None)
    if pkg is None:
        status_code = 404
        return make_response(jsonify({ 'error': 'No such package "%s"' % name }), status_code)

    for tag in ('Depends', 'Tags'):
        if tag in pkg and False:
            pkg[tag] = pkg[tag].split(', ')

    #at this point, pkg is of type debian.deb822.Packages, instead of dict.
    #that would make jsonify flip out as a TypeError. Therefore - make it dict.
    pkg = dict(pkg)
    return make_response(jsonify(pkg), status_code)

###########################################################################

_data = None


def _load_data():
    global _data

    logging.info('Proxy settings\n%s' % '\n'.join(
        sorted(('%s=%s' % (p, os.environ[p])
            for p in os.environ if 'proxy' in p))))

    all_mirrors = get_all_mirrors()

    _data = {}
    for full_source in all_mirrors:
        _read_packages(full_source)


def _read_packages(full_source):
    """ Get Packages.gz of the sources.list entry and extract all of its pks.
    Packages are saved into _data variable and will be accessed by _filter()
    function.

    @param full_source: sources.list entry (deb http//url release area1 ...)

    return: None. Content is saved into _data directly.
    """
    components = utils.deb_components(full_source)  # it leaves blanks...
    components.areas = [ a for a in components.areas if a.strip() ]
    if not components.url:
        msg = ' - Wrong mirror format!\n'
        msg += '  - Expected "deb http://mirror.url release ares"\n'
        msg += '  - Mirror provided: %s' % (full_source)
        raise RuntimeError(msg)

    # Reference:
    # https://github.com/raumkraut/python-debian/blob/master/README.deb822
    repo = '%s/dists/%s/%%s/%%s/Packages.gz' % (components.url, components.release)
    for area in components.areas:
        for arch in ('binary-all', 'binary-arm64'):
            retrieveURL = repo % (area, arch)
            BP.logger.info('Loading/processing "%s"' % retrieveURL)
            pkgresp = HTTP_REQUESTS.get(retrieveURL)
            if pkgresp.status_code != 200:
                BP.logger.error('%s not found' % arch)
                continue
            BP.logger.debug('Uncompressing %s bytes' % pkgresp.headers['content-length'])

            unzipped = gzip.decompress(pkgresp.content) # bytes all around
            BP.logger.debug('Parsing %d bytes of package data' % len(unzipped))
            unzipped = BytesIO(unzipped)    # the next step needs read()
            tmp = [ src for src in Packages.iter_paragraphs(unzipped) ]

            _data.update(dict((pkg['Package'], pkg) for pkg in tmp))


def get_all_mirrors():
    """
        Return a list of sources.list entries from the tmms config parameters.
    """
    mirror = BP.config['DEBIAN_MIRROR']
    release = BP.config['DEBIAN_RELEASE']
    areas = list(BP.config['DEBIAN_AREAS'])
    areas = ' '.join(areas)

    main_source = 'deb {url} {release} {areas}'.format(
                                    url=mirror,release=release, areas=areas)

    all_mirrors = list(BP.config['OTHER_MIRRORS']) # clone it by using list()!
    #unlikly, but someone might use set instead of list. Thus - make it a list.
    if isinstance(all_mirrors, set):
        all_mirrors = list(all_mirrors)

    if isinstance(all_mirrors, str): #can be str or list of mirrors
        all_mirrors = [all_mirrors]  #make it A list to loop through

    all_mirrors.append(main_source)
    return all_mirrors


def _filter(packages):    # Maybe it's time for a class
    return [ pkg for pkg in packages if (
        not pkg.startswith('http://') and
        not pkg.startswith('https://') and
        not pkg.startswith('file:///') and	# yes three slashes
        pkg not in _data)]


def register(url_prefix):
    BP.filter = _filter     # So manifest can see it
    BP.mainapp.register_blueprint(BP, url_prefix=url_prefix)
    _load_data()
