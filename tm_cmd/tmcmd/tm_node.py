#!/usr/bin/python3 -tt
from pdb import set_trace
import os
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
            'unsetnode':    self.delete
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

    def show(self, target, **options):
        """
        getnode <name>

        Show the manifest name that the specified node is currently
        bound to use at next boot.
        """
        super().show(target, **options)
        node_coord = self.show_name
        if node_coord.startswith('/'):	# assist humans: allow an integer
            node_coord = node_coord[1:]
        api_url = "%s%s%s" % (self.url, 'node/', node_coord)
        data = self.http_request(api_url)
        return self.to_json(data)

    def set_node(self, target, **options):
        """
        setnode <node name> <manifest>

        Select the manifest for the specified node and construct a kernel
        and root FS that the node will use the next time it boots.
        """
        assert len(target) >= 2, \
            'Missing argument: setnode <node coordinate> <manifest>'
        node_coord, manifest = target[:2]
        assert node_coord.startswith('/'), 'Illegal node coordinate'
        payload = '{ "manifest" :  "%s" }' % manifest
        api_url = '%s/%s/%s' % (self.url, 'node/', node_coord[1:])
        clean_url = os.path.normpath(api_url.split('http://')[-1])
        api_url = 'http://' + clean_url
        data = self.http_request(api_url, payload=payload)
        return self.to_json(data)

    def delete(self, target, **options):
        """
        unsetnode <node coord>

        Remove the node binding. When the node is rebooted, there will not
        be an operating system or root file system made available to it.
        The manifest remains on the system for future bindings.
        """
        super().delete(target, **options)
        node_coord = self.show_name     # should be legal by now
        if node_coord.startswith('/'):	# assist humans: allow an integer
            node_coord = node_coord[1:]
        api_url = '%s%s/%s' % (self.url, 'node/', node_coord)
        data = self.http_delete(api_url)
        return self.to_json(data)
