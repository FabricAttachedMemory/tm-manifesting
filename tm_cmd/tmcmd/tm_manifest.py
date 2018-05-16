#!/usr/bin/python3 -tt
"""
  This class inherits from tm_base.py class and is used to handle "manifest"
related operations, such as list, create, download manifests and etc.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"

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
            'list':     self.listall,
            'get':      self.show,
            'put':      self.upload,
            'delete':   self.delete
        }

    def listall(self, arg_list=None, **options):
        """
        list

        List all available manifests uploaded to the server.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'manifest/')

        data = self.http_request(url)
        return self.to_json(data)

    def show(self, target, **options):
        """
        get <prefix/manname> [file-to-save-into]

        Download a the specified manifest from the server to a file.
        (file-to-save-into) is an optional second parameter if you want to save
        manifest into a file. Otherwise, it will only display manifest contents
        on the screen.
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
        put <name/space/prefix> <manifest file>

        Select the manifest for the specified node and construct a kernel
        and root FS that the node will use the next time it boots.
        """
        # This violates the ERS but it's silly to mandate an argument that
        # can be empty when the condition can be detected unambiguously.
        # The ERS-specified method still works.
        if len(target) == 1 and os.path.isfile(target[0]):
            target.insert(0, '')	# null prefix
        assert len(target) == 2, \
            'Missing argument: put [prefix] filename'
        file_real_path = os.path.realpath(target[1])

        with open(file_real_path, 'r') as file_obj:
            manifest_content = file_obj.read()

        try:
            payload = json.loads(manifest_content)
        except ValueError as err:
            return self.to_json({
                'error': 'File does not appear to be valid JSON.'})

        api_url = '%s/%s/%s' % (self.url, 'manifest/', target[0])
        clean_url = os.path.normpath(api_url.split('http://')[1])
        api_url = 'http://' + clean_url + '/'

        data = self.http_upload(api_url, payload=payload)
        return self.to_json(data)

    def delete(self, target, **options):
        """
        delete <manifest name>

        Deletes an existing manifest from the service. Note that this
        simply deletes the manifest itself.  Any nodes configured to use the
        manifest will continue to boot using the kernel and root file system.
        """
        super().show(target, **options)
        api_url = "%s%s%s" % (self.url, 'manifest/', self.show_name.strip('/'))
        data = self.http_delete(api_url)
        return self.to_json(data)
