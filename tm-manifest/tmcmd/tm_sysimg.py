#!/usr/bin/python3 -tt
import os
import urllib
import requests
from pdb import set_trace
from . import tm_base

class TmSysImg(tm_base.TmCmd):
    """
        Admin class that intent to be hidden from a non-admin user.
    """
    def __init__(self):
        """
            Define 'args' for this class.
        """
        super().__init__()
        self.args = {
            'listsysimgs' : self.listall,
            'showsysimg' : self.show,
            'downloadsysimg' : self.download
        }


    """
        List all the TAR'ed system images located on the server.
    """
    def listall(self, arg_list=None, **options):
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'sys-image/')
        data = self.http_request(url)
        return self.to_json(data)


    """
        Show TAR'ed system image information.
    """
    def show(self, target, **options):
        super().show(target, **options)
        # return self.to_json({'error' : 'Not Implemented!'})
        return None

    """
        Download a targeted tar image to the destination on the local disk.
    """
    def download(self, target, **options):
        super().show(target, **options)
        if len(target) < 2:
            destination = '/tmp/%s' % (target[0])       
        else:
            destination = target[1]

        url = os.path.join("%s%s%s" % (self.url, 'sys-image/', self.show_name))
        self.http_download(url, destination)

        return self.to_json({ target[0] : "downloaded to %s" % (destination) })
