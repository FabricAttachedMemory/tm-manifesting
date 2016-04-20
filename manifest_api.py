#!/usr/bin/python3 -tt

import os
import sys
from pdb import set_trace

from flask import Flask, render_template, request, jsonify
from jinja2.environment import create_cache

mainapp = Flask('tm_manifesting', static_url_path='/static')
mainapp.config.from_object('manifest_config')
mainapp.config['API_VERSION'] = 1.0

###########################################################################
# Must come after mainapp config loading because it's Mobius circular

import blueprints.l4tm_packages.blueprint as BPB
mainapp.register_blueprint(BPB.BP, url_prefix='/manifesting')

import blueprints.nodes.blueprint as BNB
mainapp.register_blueprint(BNB.BP, url_prefix='/manifesting')

import blueprints.tasks.blueprint as BTB
mainapp.register_blueprint(BTB.BP, url_prefix='/manifesting')

# Must come last because it depends on validation support from others
import blueprints.manifests.blueprint as BMB
mainapp.register_blueprint(BMB.BP, url_prefix='/manifesting')

import blueprints.sysimage.blueprint as BIB
mainapp.register_blueprint(BIB.BP, url_prefix='/manifesting')

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
        return _response_bad('I see no JSON here', 406)
    version = -1.0
    for elem in hdr_accept.split(';'):
        if 'version' in elem:
            try:
                version = float(elem.split('=')[-1])
                break
            except Exception as e:
                pass
    if version < 0:
        return _response_bad('I see no version here')
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
