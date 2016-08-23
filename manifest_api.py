#!/usr/bin/python3 -tt

# Implement The Machine Manifesting API per the software ERS.  Human-readable
# web pages are also provided for the bulk of the official APIs.

import argparse
import glob
import netifaces as NIF
import os
import sys
import time

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
    from tmms.setup import parse_cmdline_args
    from tmms.utils.utils import piper
    from tmms.utils.file_utils import make_dir
    from tmms.configs.build_config import ManifestingConfiguration
except ImportError as e:
    raise SystemExit(
        'Cannot find Python module "tmms"; run "setup.py" and retry.')

###########################################################################
# Set config variables for future use across the blueprints.

cmdline_args = parse_cmdline_args('n/a')

try:
    manconfig = ManifestingConfiguration(cmdline_args.config)
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
    cmdline_args.verbose if sys.stdin.isatty() else 0
mainapp.config['DEBUG'] = cmdline_args.debug and sys.stdin.isatty()
mainapp.config['DRYRUN'] = cmdline_args.dry_run
mainapp.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0     # For node ESP files

###########################################################################
# Must come after mainapp setup because Mobius

paths = sorted([p for p in glob.glob('blueprints/*')])
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
    if 'api' not in request.path:   # Ignore versioning/JSON for HTML
        return None
    hdr_accept = request.headers['Accept']
    if 'application/json' not in hdr_accept:
        return _response_bad('I see no JSON in header/accept.', 406)
    version = -1.0
    for elem in hdr_accept.split(';'):
        if 'version' in elem:
            try:
                version = float(elem.split('=')[-1])
                break
            except Exception as e:
                pass
    if version < 0:
        return _response_bad('I see no version here.', 406)
    want = mainapp.config['API_VERSION']
    if version != want:
        return _response_bad('Bad version: %s != %s' % (version, want))


@mainapp.after_request
def version(response):
    if 'api' in request.path:   # Ignore versioning/JSON for HTML
        response.headers['Content-Type'] = \
            'application/json;version=%s' % mainapp.config['API_VERSION']
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
# Networking stuff


def _read_iptables_config(config):
    format_path = '%(DNSMASQ_CONFIGS)s/%(PXE_INTERFACE)s.iptables' % config
    with open(format_path, 'r') as f:
        action_format = f.read()
    return action_format


def clear_iptables(config):
    action_format = _read_iptables_config(config)
    delrules = action_format.format(action='D').split('\n')
    for d in delrules:  # Delete them until they're gone
        if not d or d.startswith('#'):
            continue
        cmd = 'iptables ' + d
        ret = 0
        while not ret:
            ret, stdout, stderr = piper(cmd)
    return action_format


def set_iptables(config):
    '''This will actually insert rules regardless of existence of interface.'''
    action_format = clear_iptables(config)
    addrules = action_format.format(action='A').split('\n')
    for a in addrules:
        if not a or a.startswith('#'):
            continue
        cmd = 'iptables ' + a
        ret, stdout, stderr = piper(cmd)
        if ret:
            raise RuntimeError('%s failed: %s' % (cmd, stderr))
    return action_format


def start_dnsmasq(config):
    pxe_interface = config['PXE_INTERFACE']
    if pxe_interface not in NIF.interfaces():
        print('%s does not exist; cannot start dnsmasq.' % pxe_interface,
            file=sys.stderr)
        return None
    make_dir('/var/log/tmms')   # FIXME: local to MANIFEST_ROOT/flotsam
    make_dir('/var/run/tmms')
    conf_file = '%(DNSMASQ_CONFIGS)s/%(PXE_INTERFACE)s.conf' % config
    p = piper('dnsmasq --conf-file=%s' % conf_file, return_process_obj=True)
    time.sleep(1)
    if p.poll() is not None:    # it quit for some reason
        print('dnsmasq did not (re)-start.', file=sys.stderr)
        return None
    return p


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

    create_loopback_files()     # disappear after reboot
    set_iptables(mainapp.config)
    dnsmasq_proc = start_dnsmasq(mainapp.config)
    mainapp.run(
        debug=mainapp.config['DEBUG'],
        use_reloader=True,
        host=mainapp.config['HOST'],
        port=mainapp.config['PORT'],
        threaded=False)
