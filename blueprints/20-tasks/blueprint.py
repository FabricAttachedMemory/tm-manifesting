'''L4TM Tasks'''

import os
import sys
from debian.deb822 import Packages
from pdb import set_trace

from flask import Blueprint, render_template, request, jsonify

_ERS_element = 'task'

# See the README in the main templates directory.
BP = Blueprint(_ERS_element, __name__)

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/%s/' % _ERS_element)
@BP.route('/%s/<name>' % _ERS_element)
def webpage(name=None):

    if name is None:
        return render_template(
            _ERS_element + '_all.tpl',
            label=__doc__,
            keys=sorted(_data.keys()),
            url_base=request.url)

    return render_template(
        _ERS_element + '.tpl',
        label=__doc__,
        name=name,
        itemdict=_data[name])

###########################################################################
# API
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/api/%s/' % _ERS_element)
@BP.route('/api/%s/<name>' % _ERS_element)
def api(name=None):
    if name is None:
        tasks = [ ]
        for task in _data.values():
            tmpdict = {
                'task': task['Task'],
                'key': task['Key'],
                'description': task['Description']
            }
            tasks.append(tmpdict)
        return jsonify({ 'task': tasks })

    task = _data.get(name, None)
    if task is None:
        return jsonify({ 'error': 'No such task "%s"' % name })
    for tag in ('Depends', 'Tags'):
        if tag in task and False:
            set_trace()
            task[tag] = task[tag].split(', ')
    return jsonify(task)

###########################################################################

_data = None

def _load_data():
    '''Parse the actual tasksel description file.'''
    global _data

    _data = { }
    set_trace()
    with open(mainapp.root_path + '/L4TM.desc', 'r') as f:
        tmp = [ task for task in Packages.iter_paragraphs(f) ]
        _data.update(dict((task['Task'], task) for task in tmp))


def _filter(tasks):    # Maybe it's time for a class
    return [ task for task in tasks if task not in _data ]


def register(junk):
    BP.config = mainapp.config
    BP.filter = _filter     # So manifest can see it
    mainapp.register_blueprint(BP, url_prefix=BP.config['url_prefix'])
    _load_data()
