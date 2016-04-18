#/usr/bin/python3 -tt

import requests as HTTP_REQUESTS
import json
from pdb import set_trace

class TmCmd():

    # url ='http://rocky42.americas.hpqcorp.net:31178/manifesting/api/'
    url='http://localhost:31178/manifesting/api/'
    args = {}

    def __init__(self, sort=True, headers={}, indent=4):
        self.json_indent = indent
        self.json_sort = sort
        self.show_name = None
        if not headers:
            self.header = {'Accept' : 'application/json; version=1.0'}


    def listall(self, *args, **options):
        """
            Intended to be overridden by inherited class.
        """
        assert len(args) == 0, 'This function does not take non-optional arguments!'
        if 'verbose' in options and options['verbose']:
            print(' - Sending request to "%s"...' % url)


    def show(self, args, **options):
        """
            Intended to be overridden by inherited class.
        """
        assert len(args) >= 1, 'Missing argument: thisfunction <name>!'
        # Let user pass both types to avoid confusion passing args as "list" for a single argument.
        #Passing list is helpfull for a generic function call, (as in tm_manifest.py)
        self.show_name = args[0] if type(args) is list else args
        if 'verbose' in options and options['verbose']:
            print(' - Sending request to "%s"...' % url)

    def http_request(self, url):
        """
            Do a http request on the provided url and return a response
        in jsong format (if abailable).
        :param 'url': [str] url request.
        :return: [json]
        """
        http_resp = HTTP_REQUESTS.get(url, headers=self.header)
        jsondata = http_resp.json()
        return jsondata


    def to_json(self, content):
        """
            Convert concent to json string with class parameters.
        """
        return json.dumps(content, indent=self.json_indent, sort_keys=self.json_sort)


    def update_cmd(self, arg_dict):
        """
            Add "doc string" of each function defined in the derived from TmCmd class.
        Since it is passed by reference - there is no return value for this function.
        """
        new_keys = arg_dict.keys()
        existed_keys = self.args.keys()
        overlap = list(set(new_keys) & set(existed_keys))
        if (overlap):
            raise KeyError('Can not merge cmd args! Keys collision.')
        arg_dict.update(self.args)
