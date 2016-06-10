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
            'put' : self.upload,
            'delete' : self.delete
        }


    def listall(self, arg_list=None, **options):
        """
    SYNOPSIS
        list

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
        get <prefix/manname> (file-to-save-into)

    DESCRIPTION
            Download a manifest from the server with the specified name to the specified
        file.
        (file-to-save-into) is an optional second parameter if you want to save
        manifest into a file. Otherwise, it will only display manifest contents
        on the screen without saving.
        """
        super().show(target, **options)
        api_url = "%s%s%s" % (self.url, 'manifest/', self.show_name)
        data = self.http_request(api_url)
        if len(target) == 2:
            save_into = target[1]
            with open(save_into, 'w') as file_obj:
                file_obj.write(self.to_json(data))
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


    def delete(self, target, **options):
        """
            Not implemented
        """
        super().show(target, **options)
        api_url = "%s%s%s" % (self.url, 'manifest/', self.show_name)
        data = self.http_delete(api_url)
        return self.to_json(data)


