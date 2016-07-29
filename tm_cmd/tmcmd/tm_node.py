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
            'listnodes' : self.listall,
            'listbindings': self.listbindings,
            'getnode' : self.show,
            'setnode' : self.set_node,
            'unsetnode' : self.delete
        }


    def listall(self, arg_list=None, **options):
        """
    SYNOPSIS
        listnodes

    DESCRIPTION
        List all the available nodes in the network.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'nodes')
        data = self.http_request(url)
        return self.to_json(data)


    def listbindings(self, arg_list=None, **options):
        """
    SYNOPSIS
        listbindings

    DESCRIPTION
        List all the manifests assigned to a specific node.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'node')
        data = self.http_request(url)
        return self.to_json(data)


    def show(self, target, **options):
        """
    SYNOPSIS
        getnode <name>

    DESCRIPTION
         Show the manifest name that the specified node is currently directed to
        use at next boot.
        """
        super().show(target, **options)
        api_url = "%s%s%s" % (self.url, 'node/', self.show_name)
        data = self.http_request(api_url)
        return self.to_json(data)


    def set_node(self, target, **options):
        """
    SYNOPSIS
        setnode <node name> <manifest>

    DESCRIPTION
            Select the manifest for the specified node and construct a kernel
        and root FS that the node will use the next time it boots.
        """
        assert len(target) >= 2, 'Missing argument: setnode <node coordinate> <manifest>'
        payload = '{ "manifest" :  "%s" }' % target[1]
        api_url = '%s/%s/%s' % (self.url, 'node/', target[0])
        clean_url = os.path.normpath(api_url.split('http://')[0])
        api_url = 'http://' + clean_url
        data = self.http_request(api_url, payload=payload)
        return self.to_json(data)


    def delete(self, target, **options):
        """
    SYNOPSIS
        unsetnode <node coord>

    DESCRIPTION
            Remove the node configuration from the manifesting service. When the node
        is rebooted, there will not be an operating system or root file system made
        available to it.
        """
        super().delete(target, **options)
        node_coord = self.show_name
        api_url = '%s%s/%s' % (self.url, 'node', node_coord)
        data = self.http_delete(api_url)
        return self.to_json(data)
