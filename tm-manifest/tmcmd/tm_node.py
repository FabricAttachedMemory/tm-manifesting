#!/usr/bin/python3 -tt
from pdb import set_trace
from . import tm_base

class TmNode(tm_base.TmCmd):

    def __init__(self):
        """
            Define 'args' for this class.
        """
        super().__init__()
        self.args = {
            'listnodes' : self.listall,
            'list' : self.show,
            'setnode' : self.set_node
        }

    def listall(self, arg_list=None, **options):
        """
    SYNOPSIS
        listnodes

    DESCRIPTION
        NOT IMPLEMENTED
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'node/')
        data = self.http_request(url)
        return self.to_json(data)
        #return { 'error' : 'Not implemented.' }


    def show(self, target, **options):
        """
    SYNOPSIS
        list <name>

    DESCRIPTION
        NOT IMPLEMENTED
        """
        super().show(target, **options)
        #url = "%s%s%s" % (self.url, 'package/', self.show_name)
        #data = self.http_request(url)
        #return self.to_json(data)
        return { 'error' : 'Not implemented.' }


    def set_node(self, target, **options):
        """
    SYNOPSIS
        setnode <node name> <manifest.json>

    DESCRIPTION
        NOT IMPLEMENTED
        """
        #set_trace()
        #assert len(target) >= 2, 'Missing argument: setnode <manifest.json> <node coordinate>!'
        #payload = { 'manifest' :  target[1] }
        #api_url = "%s/%s/%s" % (self.url, 'node/', ntarget[2])
        #api_url = os.path.normpath(api_url)
        #data = self.http_request(api_url, payload=payload)
        #return self.to_json(data)
        return { 'error' : 'Not implemented.' }
