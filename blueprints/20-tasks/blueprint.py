#!/usr/bin/python3
"""L4TM Tasks
 This blueprint handles "tasks" related routines to let users list all available
tasks provided by the manifesting-server api. Quering individual task will list
its metadata: name, list of packages, manifest and etc.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


from debian.deb822 import Packages as debPackages
import flask
import os
from pdb import set_trace
import sys


_ERS_element = 'task'

# See the README in the main templates directory.
BP = flask.Blueprint(_ERS_element, __name__)

###########################################################################
# HTML
# See blueprint registration in manifest_api.py, these are relative paths


@BP.route('/%ss/' % _ERS_element)       # Plural form of element name to query all tasks
@BP.route('/%s/<name>' % _ERS_element)  # Singular - to get one task.
def webpage(name=None):
    if name is None:
        return flask.render_template(
            _ERS_element + '_all.tpl',
            label=__doc__,
            keys=sorted(_data.keys()),
            base_url=flask.request.url)

    return flask.render_template(
        _ERS_element + '.tpl',
        label=__doc__,
        name=name,
        base_url=flask.request.url,
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
        return flask.jsonify({ 'task': tasks })

    task = _data.get(name, None)
    if task is None:
        return flask.jsonify({ 'error': 'No such task "%s"' % name })
    for tag in ('Depends', 'Tags'):
        if tag in task and False:
            set_trace()
            task[tag] = task[tag].split(', ')
    return flask.jsonify(task)

###########################################################################

_data = None

def _load_data():
    '''Parse the actual tasksel description file.'''
    global _data

    _data = {}
    task_content = None
    with open(BP.tasks_file, 'r') as file_obj:
        task_content = file_obj.read()

    deb_packages_iter = debPackages.iter_paragraphs(task_content)
    tmp = [ task for task in deb_packages_iter ]
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


def register(url_prefix):
    BP.filter = _filter     # So 99_manifest can see it
    BP.lookup = _lookup
    BP.get_packages = _packages
    BP.tasks_file = BP.mainapp.root_path + '/configs/L4TM.desc'
    BP.mainapp.register_blueprint(BP, url_prefix=url_prefix)
    _load_data()
