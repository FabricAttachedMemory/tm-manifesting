#!/usr/bin/python3 -tt
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
            'listsysimgs' : self.listsysimgs,
            'showsysimg' : self.showsysimg
        }


    """
        List all the TAR'ed system images located on the server.
    """
    def listsysimgs(self, *args, **options):
        url = "%s%s" % (self.url, 'sys-image/')
        data = self.http_request(url)
        return self.to_json(data)


    """
        Show TAR'ed system image information.
    """
    def showsysimg(self, args, **options):
        return self.to_json({'error' : 'Not Implemented!'})
