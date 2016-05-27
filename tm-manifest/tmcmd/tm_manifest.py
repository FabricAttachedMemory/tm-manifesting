#!/usr/bin/python3 -tt
from pdb import set_trace
import json
import os
from . import tm_base

class TmManifest(tm_base.TmCmd):

    def __init__(self):
        """
            Define 'args' for this class.
        """
        super().__init__()
        self.args = {
            'list' : self.listall,
            'get' : self.show,
            'put' : self.upload
        }


    def listall(self, arg_list=None, **options):
        """
    SYNOPSIS
        listnodes

    DESCRIPTION
        List all available manifests uploaded to the server.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'manifest/')
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


    def upload(self, target, **options):
        """
    SYNOPSIS
        put <manifest name> <manifest file>

    DESCRIPTION
            Select the manifest for the specified node and construct a kernel
        and root FS that the node will use the next time it boots.
        """
        assert len(target) >= 2, 'Missing argument: put <manifest name> <manifest file>!'
        file_real_path = os.path.realpath(target[1])

        with open(file_real_path, 'r') as file_obj:
            manifest_content = file_obj.read()

        try:
            payload = json.loads(manifest_content)
        except ValueError as err:
            return self.to_json({ 'error' : 'Incorrect file type! JSON is expected.' })

        api_url = '%s/%s/%s' % (self.url, 'manifest/', target[0])
        clean_url = os.path.normpath(api_url.split('http://')[1])
        api_url = 'http://' + clean_url + '/'

        data = self.http_upload(api_url, payload=payload)
        return self.to_json(data)
