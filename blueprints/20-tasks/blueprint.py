#!/usr/bin/python3 --t
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


@BP.route('/%ss/' % _ERS_element)       # Plural form of element name to query all tasks
@BP.route('/%s/<name>' % _ERS_element)  # Singular - to get one task.
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


@BP.route('/api/%ss/' % _ERS_element)       # Plural form of element name to query all tasks
@BP.route('/api/%s/<name>' % _ERS_element)  # Singular - to get one task.
def api(name=None):
    _load_data()
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

def _load_data(mainapp):
    '''Parse the actual tasksel description file.'''
    global _data

    _data = { }
    with open(mainapp.root_path + '/configs/L4TM.desc', 'r') as f:
        tmp = [ task for task in Packages.iter_paragraphs(f) ]
        _data.update(dict((task['Task'], task) for task in tmp))


def _lookup(task_name, key=None):
    return _data.get(task_name, None)


def _packages(task_name):
    task = _lookup(task_name)
    if not task:
        return None
    # Clean out new line in the beginning and end of the task['Key'] string.
    # Strip each package name of the task['Key'] list...
    packages = [pkg.strip() for pkg in task['Key'].strip().split('\n')]
    return packages


def _filter(tasks):    # Maybe it's time for a class
    return [ task for task in tasks if task not in _data ]


def register(mainapp):  # take what you like and leave the rest
    BP.filter = _filter     # So manifest can see it
    BP.lookup = _lookup
    BP.get_packages = _packages
    mainapp.register_blueprint(BP, url_prefix=mainapp.config['url_prefix'])
    _load_data(mainapp)
