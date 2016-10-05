#!/usr/bin/python3 -tt
from pdb import set_trace
import json
import os
import time

from . import tm_base


class TmNode(tm_base.TmCmd):

    def __init__(self):
        """
            Define 'args' for this class.
        """
        super().__init__()
        self.args = {
            'listnodes':    self.listall,
            'listbindings': self.listbindings,
            'getnode':      self.show,
            'setnode':      self.set_node,
            'unsetnode':    self.delete,
            'waitnode':     self.waitnode
        }

    def listall(self, arg_list=None, **options):
        """
        listnodes

        List all the available nodes in the network.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'nodes')
        data = self.http_request(url)
        return self.to_json(data)

    def listbindings(self, arg_list=None, **options):
        """
        listbindings

        List all the manifests assigned to a specific node.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'node')
        data = self.http_request(url)
        return self.to_json(data)

    def _resolve_nodes(self, nodelist):
        '''Nodelist is from command line, should be list of /bizmumble or
           coordinates or integer node numbers.'''
        nodelist = list(nodelist)
        assert nodelist, 'nodelist is empty'
        if len(nodelist) == 1 and nodelist[0].lower() == 'all':
            nodelist = json.loads(self.listall())['200']['nodes']
        newlist = []
        for node in nodelist:	        # assist humans: allow an integer
            newlist.append(node.lstrip('/'))
        return newlist

    def show(self, target, **options):
        """
        getnode <name>

        Show the manifest name that the specified node is currently
        bound to use at next boot.
        """
        super().show(target, **options)
        assert len(target) >= 1, \
            'Missing argument: unsetnode <node coordinate>'
        node_coords = self._resolve_nodes(target)
        responses = {}
        for node_coord in node_coords:
            api_url = "%s%s%s" % (self.url, 'node/', node_coord)
            data = self.http_request(api_url)
            responses[node_coord] = { data.status_code: data.text }
        if len(node_coords) == 1:
            return self.to_json(data)
        return json.dumps(responses)

    def set_node(self, target, **options):
        """
        setnode <node name> <manifest>

        Select the manifest for the specified node and construct a kernel
        and root FS that the node will use the next time it boots.
        """
        # FIXME: super() ?
        assert len(target) >= 2, \
            'Missing argument: setnode <node coordinate> <manifest>'
        node_coords = self._resolve_nodes(target[:-1])
        manifest = target[-1]
        payload = '{ "manifest" :  "%s" }' % manifest
        responses = {}
        for node_coord in node_coords:
            api_url = '%s/%s/%s' % (self.url, 'node/', node_coord)
            clean_url = os.path.normpath(api_url.split('http://')[-1])
            api_url = 'http://' + clean_url
            data = self.http_request(api_url, payload=payload)
            responses[node_coord] = { data.status_code: data.text }
        if len(node_coords) == 1:
            return self.to_json(data)   # Per the ERS
        return json.dumps(responses)

    def delete(self, target, **options):
        """
        unsetnode <node coord>

        Remove the node binding. When the node is rebooted, there will not
        be an operating system or root file system made available to it.
        The manifest remains on the system for future bindings.
        """
        super().delete(target, **options)
        assert len(target) >= 1, \
            'Missing argument: unsetnode <node coordinate>'
        node_coords = self._resolve_nodes(target)
        responses = {}
        for node_coord in node_coords:
            api_url = '%s%s/%s' % (self.url, 'node/', node_coord)
            data = self.http_delete(api_url)
            responses[node_coord] = { data.status_code: data.text }
        if len(node_coords) == 1:
            return self.to_json(data)   # Per the ERS
        return json.dumps(responses)

    def waitnode(self, target, **options):
        """
        waitnode <node coord>

        Waits for node binding status to report a value other than "building"
        such as "ready", "unbound", or "error".
        """
        assert len(target) >= 1, \
            'Missing argument: waitnode <node coordinate>'
        node_coords = self._resolve_nodes(target)
        responses = {}      # only add them when non-building state is reached
        coordset = frozenset(node_coords)
        remaining = coordset - frozenset(responses.keys())
        sleepy = 0
        while remaining:
            time.sleep(sleepy)
            for node_coord in remaining:
                time.sleep(0.1)
                resp = json.loads(self.show((node_coord,)))
                try:
                    status = resp['200']['status']  # some phase of binding
                    if status != 'building':
                        responses[node_coord] = status
                except KeyError:
                    if '204' in resp:
                        status = 'unbound'
                    elif '404' in resp:
                        status = 'unknown'
                    else:
                        status = 'error'
                    responses[node_coord] = status
            remaining = coordset - frozenset(responses.keys())
            sleepy = 5
        return json.dumps({'200': responses})   # Just like other commands
