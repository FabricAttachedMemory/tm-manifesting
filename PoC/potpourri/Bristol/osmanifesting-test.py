#!/usr/bin/env python

######################################################################
#
# This is unit tests of OS Manifesting.
#
# @author Herry (herry.herry@hpe.com)
# @created July 2016
#
# Requirements:
# - Python 2.7 (not tested on Python 3.x)
# - Requests (`pip install requests`)
#
# To run:
# $ python osmanifesting-test.py
#
######################################################################

from __future__ import print_function
import json
import requests
import sys
import time

host = '16.25.173.240'
port = 31178
base = 'manifesting/api/'
baseUrl = "http://%s:%s/%s" % (host, port, base)
manifestUrl = "%smanifest/" % baseUrl
nodeUrl = "%snode/" % baseUrl

manifest = {'_comment': 'a dummy manifest',
            'name': 'L4TM_Spark',
            'description': 'a dummy manifest for testing',
            'release': 'testing',
            'tasks': ['L4TM_Spark'],
            'packages': []}

prefixes = ["", "prefix/", "foo/bar/"]

headers = {'Accept': 'application/json; version=1.0', 'Content-Type': 'application/json; charset=utf-8; version=1.0'}

coordinates = [
    "/machine_rev/1/datacenter/pa1/frame/A1.above_floor/rack/1/enclosure/1/node/1",
    "/machine_rev/1/datacenter/pa1/frame/A1.above_floor/rack/1/enclosure/1/node/2"
]

# waiting time until the node manifest association is ready
timeout = 120 # in seconds

# total integration tests
total_integration_tests = 5

def delete_node_manifest_association(coordinate):
    print("Deleting node manifest association of %s ..." % coordinate, end="")
    if coordinate[0] == '/':
        coordinate = coordinate[1:]
    url = nodeUrl + coordinate
    r = requests.delete(url, headers=headers)
    if r.status_code >= 200 and r.status_code < 300:
        try:
            r = requests.get(nodeUrl, headers=headers)
            if r.status_code == 204 or (r.status_code >= 200 and r.status_code < 300 and coordinate not in r.json()['mappings'].keys()):
                print("[OK]")
                return True
            else:
                print("[Error101]\nNode manifest association is not deleted properly\nStatus code of GET %s is '%s'\nbody: %s" % (nodeUrl, r.status_code, r.text), end="\n\n")
                sys.exit(101)
        except:
            print("[Error102]\nNode manifest association is not deleted properly\nStatus code of GET %s is '%s'\nbody: %s" % (nodeUrl, r.status_code, r.text), end="\n\n")
            sys.exit(102)
    else:
        print("[Error103]\nFailed to delete node manifest association\nmethod: DELETE\nurl: %s\nstatus code: %s" % (url, r.status_code), end="\n\n")
        sys.exit(103)
    return False

def delete_manifest(manifest):
    print("Deleting manifest %s ..." % manifest, end='')
    url = manifestUrl + manifest
    r = requests.delete(url, headers=headers)
    if (r.status_code >= 200 and r.status_code < 300) or r.status_code == 404:
        r = requests.get(url, headers=headers)
        if r.status_code == 404:
            print("[OK]")
            return True
        else:
            print("[Error201]\nManifest is not deleted properly\nStatus code of GET %s is '%s'\nbody: %s" % (url, r.status_code, r.text), end="\n\n")
            sys.exit(201)
    else:
        print("[Error202]\nFailed to delete manifest\nmethod: DELETE\nurl: %s\nstatus code: %s" % (url, r.status_code), end="\n\n")
        sys.exit(202)
    return False

def post_manifest(prefix, manifest):
    print("Uploading manifest %s%s ..." % (prefix, manifest['name']), end="")
    url = manifestUrl + prefix
    data = json.dumps(manifest, separators=(',', ':'))
    r = requests.post(url, data, headers=headers)
    if r.status_code >= 200 and r.status_code < 300:
        r = requests.get(manifestUrl, headers=headers)
        try:
            if r.status_code >= 200 and r.status_code < 300 and manifest['name'] in r.json()['manifests']:
                print("[OK]")
                return True
            else:
                print("[Error301]\nManifest '%s' is not uploaded properly\nuploaded manifests: %s" % (manifest['name'], r.text), end="\n\n")
                sys.exit(301)
        except:
            print("[Error302]\nManifest '%s' is not uploaded properly\nuploaded manifests: %s" % (manifest['name'], r.text), end="\n\n")
            sys.exit(302)
    else:
        print("[Error303]\nFailed uploading manifest\nmethod: POST\nurl: %s\ndata: %s\nresponse code: %s" % (url, data, r.status_code), end="\n\n")
        sys.exit(303)
    return False

def put_node_manifest(coordinate, manifest):
    print("Associating %s to manifest '%s'..." % (coordinate, manifest), end="")
    if coordinate[0] == '/':
        coordinate = coordinate[1:]
    url = nodeUrl + coordinate
    data = json.dumps({'manifest': manifest}, separators=(',', ':'))
    r = requests.put(url, data, headers=headers)
    if r.status_code >= 200 and r.status_code < 300:
        time.sleep(1)
        try:
            r = requests.get(nodeUrl, headers=headers)
            if r.status_code == 200 and r.json()['mappings'][coordinate]['manifest'] == manifest:
                print("[OK]")
                return True
            else:
                print("[Error401]\nNode manifest association is not deleted properly\nStatus code of GET %s is '%s'\nbody: %s" % (nodeUrl, r.status_code, r.text), end="\n\n")
                sys.exit(401)
        except:
            print("[Error402]\nNode manifest association is not deleted properly\nStatus code of GET %s is '%s'\nbody: %s" % (nodeUrl, r.status_code, r.text), end="\n\n")
            sys.exit(402)
    else:
        print("[Error403]\nFailed to associate a manifest to a node\nmethod: PUT\nurl: %s\ndata: %s\nstatus code: %s" % (url, data, r.status_code), end="\n\n")
        sys.exit(403)
    return False

def integration_test():
    """
    Perform an integration test against OS Manifesting service.
    """

    # clear node manifest associations
    print("--- Clear node manifest associations ---")
    for coordinate in coordinates:
        delete_node_manifest_association(coordinate)

    # clear manifests
    print("--- Clear manifests ---")
    for prefix in prefixes:
        m = "%s%s" % (prefix, manifest['name']) if prefix != '' else manifest['name']
        delete_manifest(m)

    # upload manifests
    print("--- Upload manifests ---")
    for prefix in prefixes:
        post_manifest(prefix, manifest)

    # associate manifest to node
    print("--- Associate manifest to node ---")
    for i in range(0, len(coordinates)):
        prefix = prefixes[i]
        m = "%s%s" % (prefix, manifest['name']) if prefix != '' else manifest['name']
        put_node_manifest(coordinates[i], m)

    # within 120 seconds, wait until the associations' status to be 'ready'
    print("--- within 120 seconds, wait until all node associations are 'ready' ---")
    all_ready = False
    for i in range(1, timeout):
        time.sleep(1)
        print('.', end='')
        sys.stdout.flush()
        r = requests.get(nodeUrl, headers=headers)
        all_ready = True
        if r.status_code == 200:
            mappings = r.json()['mappings']
            for coordinate in coordinates:
                if coordinate[0] == '/':
                    coordinate = coordinate[1:]
                '''
                if mappings[coordinate]['status'] == 'error':
                    print("\n[Error501] Status of node manifest association %s is 'error'" % coordinate, end="\n\n")
                    sys.exit(501)
                '''
                if mappings[coordinate]['status'] != 'ready':
                    all_ready = False
                    break
        if all_ready:
            break
    if all_ready:
        print("\nAll node manifest associations are ready within %s seconds" % timeout)
    else:
        print("\n[Error502] Some node manifest associations are not ready within %s seconds" % timeout, end="\n\n")
        sys.exit(502)

def main():
    for i in range(0, total_integration_tests):
        print("=== Integration Test #%s ===" % i)
        sys.stdout.flush()
        integration_test()
        print("=== End of Integration Test #%s ===" % i, end="\n\n")

if __name__ == '__main__':
    main()
