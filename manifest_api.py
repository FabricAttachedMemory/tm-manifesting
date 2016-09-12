#!/usr/bin/python3 -tt

# Implement The Machine Manifesting API per the software ERS.  Human-readable
# web pages are also provided for the bulk of the official APIs.

import argparse
import glob
import netifaces as NIF
import os
import psutil
import signal
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
    from tmms.utils.utils import piper, create_loopback_files
    from tmms.utils.logging import tmmsLogger
    from tmms.utils.file_utils import make_dir
    from tmms.configs.build_config import ManifestingConfiguration
    from tmms.utils.daemonize3 import Daemon
except ImportError as e:
    raise SystemExit(
        'Cannot find Python module "tmms"; run "setup.py" and retry.')

###########################################################################
# Set config variables for future use across the blueprints.

cmdline_args = parse_cmdline_args('n/a')

daemon = Daemon()  # FIXME: changedir to an appropriate location
try:
    if cmdline_args.daemon_start:
        mainapp.logger.info('Daemonining the server.')
        daemon.start()

    if cmdline_args.daemon_stop:
        print('Shutting down the daemon...')
        daemon.stop()
        raise SystemExit(0)

    if cmdline_args.daemon_status:
        print(daemon.status())
        raise SystemExit(0)
except RuntimeError as err:
    raise SystemExit(str(err))

try:
    manconfig = ManifestingConfiguration(cmdline_args.config)
    tmconfig = TMConfig(manconfig['TMCONFIG'])
except Exception as e:
    raise SystemExit('Bad config file(s): %s' % str(e))

if tmconfig.errors:
    msg = 'Bad %s:\n' % manconfig['TMCONFIG'] + '\n'.join(tmconfig.errors)
    raise SystemExit(msg)

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
mainapp.config['auto-update'] = cmdline_args.auto_update
mainapp.config['DEBUG'] = cmdline_args.debug and sys.stdin.isatty()
mainapp.config['DRYRUN'] = cmdline_args.dry_run
mainapp.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0     # For node ESP files

# Flask has configured a root logger with default "DEBUG" level handler that
# spits to stderr.  That's good enough for early work.  tmmsLogger will
# change that behavior on first invocation.
mainapp.config['LOGFILE'] = '/var/log/tmms.%s.log' % (
    mainapp.config['PXE_INTERFACE'])

###########################################################################
# Must come after mainapp setup because there's an almost circular (more
# like Mobius) relationship between importing and registering a blueprint.


def register_blueprints(mainapp):
    paths = sorted([p for p in glob.glob('blueprints/*')])
    if not paths:
        raise SystemExit('Cannot find any blueprints')
    ngood = 0

    for p in paths:
        try:
            modspec = p.replace('/', '.') + '.blueprint'
            mainapp.logger.info('Importing %s' % modspec)
            imported = import_module(modspec)

            # Set commonly used globals or convenience attributes.  Each
            # imported BP has its own BP global, used as the route decorator
            # within the module.  Flask is weird that way.
            imported.BP.mainapp = mainapp
            imported.BP.blueprints = mainapp.blueprints   # inter-BP use
            imported.BP.config = mainapp.config
            imported.BP.VERBOSE = mainapp.config['VERBOSE']
            imported.BP.DEBUG = mainapp.config['DEBUG']
            name = imported.BP.name
            imported.BP.logger = tmmsLogger(name)

            # Let each blueprint add its local attributes, then register
            # itself against the flask framework using its "BP.mainapp".
            imported.register(mainapp.config['url_prefix'])
            imported.BP.logger.info('blueprint registration complete')
            ngood += 1
        except ImportError as e:
            mainapp.logger.critical('import(%s) failed: %s' % (p, str(e)))
            if mainapp.config['DEBUG']:
                set_trace()
            pass
        except AttributeError as e:
            mainapp.logger.critical('register(%s) failed: %s' % (p, str(e)))
        except Exception as e:
            mainapp.logger.critical('blueprint %s failed: %s' % (p, str(e)))

    if ngood != len(paths):
        msg = 'Not all blueprints finished registration'
        mainapp.logger.critical(msg)
        raise SystemExit(msg)

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
        release=mainapp.config['L4TM_RELEASE'],
        rules=mainapp.config['rules'],
        url_root=request.url_root,
        coordinate=mainapp.config['tmconfig'].racks[1]['coordinate'])

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


def kill_pid(pid, procname='', daemon=True):      # FIXME: utils?
    if pid not in psutil.pids():
        return False
    for p in psutil.process_iter():
        if p.pid != pid:
            continue
        if procname and p.name() != procname:
            continue
        if daemon and p.ppid() != 1:
            continue
        mainapp.logger.info('Killing PID %d' % pid)
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
        if pid in psutil.pids():    # SIGTERM needs a boost
            try:
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            except ProcessLookupError:  # SIGTERM was enough after all
                pass
        return True
    return False


def kill_dnsmasq(config):
    # There can be more than one bound to it, especially if libvirt was used..
    # Easy way: started from (previous) run of manifest_api.
    try:
        with open(config['DNSMASQ_PIDFILE'], 'r') as f:
            pid = int(f.read())
        kill_pid(pid, 'dnsmasq')
    except Exception:   # a valiant effort in vain
        pass

    # Hard way: track down dnsmasq(s) attached to the configured interface.
    pxe_interface = config['PXE_INTERFACE']
    if pxe_interface not in NIF.interfaces():
        return
    tmp = NIF.ifaddresses(pxe_interface).get(NIF.AF_INET, None)
    if tmp is None:         # ASS-U-MES "torms" address bound here
        return
    pxe_addr = tmp[0]['addr']
    openconns = [(c.laddr[1], c.pid)    # port, pid
        for c in psutil.net_connections(kind='inet4')
            if c.laddr[0] == pxe_addr]
    ports = set(c[0] for c in openconns)
    pids = set(c[1] for c in openconns)
    # libvirt bridge will always have DNS (53).  A truly simple net definition
    # won't have TFTP (69) but others might.  Obviously one started from here
    # will have TFTP.
    if ports.issubset(set((53, 69))):
        while len(pids):
            pid = pids.pop()
            kill_pid(pid, 'dnsmasq')


def start_dnsmasq(config):
    pxe_interface = config['PXE_INTERFACE']
    if pxe_interface not in NIF.interfaces():
        mainapp.logger.critical('%s does not exist; cannot start dnsmasq.')
        return False

    conf_file = '%(DNSMASQ_CONFIGS)s/%(PXE_INTERFACE)s.conf' % config

    # This is configured to daemonize so a p.poll() will not show it as active.
    p = piper('dnsmasq --conf-file=%s' % conf_file, return_process_obj=True)
    time.sleep(0.5)
    p.poll()    # Does a wait() on a daemonizing process to release it
    return True

###########################################################################
# Must come after all route declarations, including blueprint registrations.
# Used here for debug and in landing page (see route above).

if __name__ == '__main__':
    mainapp.config['rules'] = sorted(
        '%s %s' % (rule.rule, rule.methods) for
            rule in mainapp.url_map.iter_rules())
    for rule in mainapp.config['rules']:
        mainapp.logger.debug(rule)

    # http://flask.pocoo.org/docs/0.10/api/#application-object; options at
    # http://werkzeug.pocoo.org/docs/0.11/serving/#werkzeug.serving.run_simple

    if mainapp.config['DEBUG']:
        mainapp.jinja_env.cache = create_cache(0)

    register_blueprints(mainapp)
    create_loopback_files() # they disappear after LXC restart FIXME utils?
    set_iptables(mainapp.config)
    kill_dnsmasq(mainapp.config)
    if not start_dnsmasq(mainapp.config):   # It's okay to leave it running
        raise SystemExit('Cannot start dnsmasq')

    # NOW daemonize

    mainapp.logger.info('Starting web server')
    mainapp.run(
        debug=mainapp.config['DEBUG'],
        use_reloader=mainapp.config['auto-update'],
        host=mainapp.config['HOST'],
        port=mainapp.config['PORT'],
        threaded=False)
    mainapp.logger.warning('Built-in server terminated')
