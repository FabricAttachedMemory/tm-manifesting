#!/usr/bin/python3 -tt

import glob
import os
import sys
from importlib import import_module
from pdb import set_trace

from flask import Flask, render_template, request, jsonify
from jinja2.environment import create_cache

# Assumes tm_librarian.deb installs in normal sys.path place
from tm_librarian.tmconfig import TMConfig

###########################################################################
# Everything is global until I figure out decorators on class methods

mainapp = Flask('tm_manifesting', static_url_path='/static')
mainapp.config.from_object('configs.manifest_config')
mainapp.config['url_prefix'] = '/manifesting'

try:
    mainapp.config['tmconfig'] = TMConfig(mainapp.config['TMCONFIG'])
except Exception as e:
    mainapp.config['tmconfig'] = TMConfig('configs/hpetmconfig.json')

###########################################################################
# Must come after mainapp setup because Mobius

paths = sorted([ p for p in glob.glob('blueprints/*') ])
if not paths:
    raise SystemExit('Cannot find any blueprints')
n = 0

mainapp.VERBOSE = mainapp.config['VERBOSE']  # lower cased already taken
mainapp.DEBUG = mainapp.config['DEBUG']      #

for p in paths:
    try:
        modspec = p.replace('/', '.') + '.blueprint'
        BP = import_module(modspec)
        BP.register(mainapp)
        n += 1
    except ImportError as e:
        set_trace()
        print('No blueprint at %s' % p, file=sys.stderr)
    except AttributeError as e:
        print('blueprint at %s has no register()' % p, file=sys.stderr)
    except Exception as e:
        print('blueprint at %s failed: %s' % (p, e), file=sys.stderr)

if n != len(paths):
    raise SystemExit('Not all blueprints finished registration')

###########################################################################
# Global header handling


def _response_bad(errmsg, status_code=418):
    response = jsonify({'error': errmsg})
    response.status_code = status_code
    return response


@mainapp.before_request
def check_version(*args, **kwargs):
    if 'api' not in request.path:   # Ignore versioning for HTML
        return None
    hdr_accept = request.headers['Accept']
    if 'application/json' not in hdr_accept:
        return _response_bad('I see no JSON here. Did you forget "application/json" in request header?', 406)
    version = -1.0
    for elem in hdr_accept.split(';'):
        if 'version' in elem:
            try:
                version = float(elem.split('=')[-1])
                break
            except Exception as e:
                pass
    if version < 0:
        return _response_bad('I see no version here. Did you forget "version=1.0" in request header?')
    want = mainapp.config['API_VERSION']
    if version != want:
        return _response_bad('Bad version: %s != %s' % (version, want))


@mainapp.after_request
def version(response):
    response.headers['Content-Type'] += ';version=%s' % mainapp.config['API_VERSION']
    return response

###########################################################################
# Top-level routing


@mainapp.route('/manifesting/')
def root():
    return render_template(
        'index.tpl',
        api_version=mainapp.config['API_VERSION'],
        base_url=request.base_url,
        mirror=mainapp.config['L4TM_MIRROR'],
        rules=mainapp.config['rules'],
        url_root=request.url_root)

###########################################################################
# Must come after all route declarations, including blueprint registrations

mainapp.config['rules'] = sorted('%s %s' % (rule.rule, rule.methods) for
    rule in mainapp.url_map.iter_rules())

if __name__ == '__main__':
    for rule in mainapp.config['rules']:
        print(rule)

    # http://flask.pocoo.org/docs/0.10/api/#application-object; options at
    # http://werkzeug.pocoo.org/docs/0.11/serving/#werkzeug.serving.run_simple

    if mainapp.config['DEBUG']:
        mainapp.jinja_env.cache = create_cache(0)
    mainapp.run(
        debug=mainapp.config['DEBUG'],
        use_reloader=True,
        host=mainapp.config['HOST'],
        port=mainapp.config['PORT'],
        threaded=False)
