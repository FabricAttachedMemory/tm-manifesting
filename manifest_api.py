#!/usr/bin/python3 -tt

# Implement The Machine Manifesting API per the software ERS.  Human-readable
# web pages are also provided for the bulk of the official APIs.

import argparse
import glob
import os
import sys
from importlib import import_module
from pdb import set_trace

assert os.geteuid() == 0, 'This program requires root permissions'

from flask import Flask, render_template, request, jsonify
from jinja2.environment import create_cache

# Assumes tm_librarian.deb installs in normal sys.path place
from tm_librarian.tmconfig import TMConfig

# For running from git repo, setup.py does the right thing.  True .deb
# installation will also do the right thing.
try:
    from tmms.utils import utils
    from tmms.configs.build_config import ManifestingConfiguration
except ImportError as e:
    raise SystemExit(
        'Cannot find Python module "tmms"; run "setup.py" and retry.')

###########################################################################


def parse_args():
    """ Parse system arguments set from command line."""
    parser = argparse.ArgumentParser(
        description='Manifesting API server runtime settings')
    ManifestingConfiguration.parser_add_config(parser)
    parser.add_argument('--verbose', help='Make it talk.',
                        type=int, default=0)
    parser.add_argument('--debug', help='Turn on flask debugging',
                        action='store_true')
    parser.add_argument('--dry-run', help='No action; simulation of events.',
                        action='store_true')
    args, _ = parser.parse_known_args()
    print('Using config file', args.config)
    return vars(args)

###########################################################################
# Set config variables for future use across the blueprints.

cmdline_args = parse_args()
if cmdline_args['config'] is None:
    this_file = os.path.realpath(__file__)
    cmdline_args['config'] = os.path.dirname(this_file) + '/manifest_config.py'

try:
    manconfig = ManifestingConfiguration(cmdline_args['config'])
except Exception as e:
    raise SystemExit(str(e))

tmconfig = TMConfig(manconfig['TMCONFIG'])
if tmconfig.errors:
    raise SystemExit('Bad TMCF:\n' + '\n'.join(tmconfig.errors))

# mainapp is needed as decorator base so it comes early.
# Flask sets mainapp.root_path to cwd.  Set that now; it's also needed
# during blueprint scanning.

os.chdir(os.path.dirname(os.path.realpath(__file__)))
mainapp = Flask('tm_manifesting', static_url_path='/static')
mainapp.config.update(manconfig)
mainapp.config['tmconfig'] = tmconfig

mainapp.config['API_VERSION'] = 1.0
mainapp.config['url_prefix'] = '/manifesting'
mainapp.config['VERBOSE'] = \
    cmdline_args['verbose'] if sys.stdin.isatty() else 0
mainapp.config['DEBUG'] = cmdline_args['debug'] and sys.stdin.isatty()
mainapp.config['DRYRUN'] = cmdline_args['dry_run']

###########################################################################
# Must come after mainapp setup because Mobius

paths = sorted([ p for p in glob.glob('blueprints/*') ])
if not paths:
    raise SystemExit('Cannot find any blueprints')
ngood = 0

for p in paths:
    try:
        modspec = p.replace('/', '.') + '.blueprint'
        BP = import_module(modspec)
        BP.BP.VERBOSE = mainapp.config['VERBOSE']  # lower cased already taken
        BP.BP.DEBUG = mainapp.config['DEBUG']      #
        BP.register(mainapp)
        ngood += 1
    except ImportError as e:
        set_trace()
        print('No blueprint at %s' % p, file=sys.stderr)
    except AttributeError as e:
        print('blueprint at %s has no register()' % p, file=sys.stderr)
    except Exception as e:
        print('blueprint at %s failed: %s' % (p, e), file=sys.stderr)

if ngood != len(paths):
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
        return _response_bad('I see no version here. Did you forget "version" in request header?')
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
