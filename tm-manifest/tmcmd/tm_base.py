#/usr/bin/python3 -tt

import requests as HTTP_REQUESTS
import json
from pdb import set_trace

class TmCmd():

    # url ='http://rocky42.americas.hpqcorp.net:31178/manifesting/api/'
    url='http://localhost:31178/manifesting/api/'
    args = {}

    def __init__(self):
        self.json_indent = 4
        self.json_sort = True


    def http_request(self, url):
        """
            Do a http request on the provided url and return a response
        in jsong format (if abailable).
        :param 'url': [str] url request.
        :return: [json]
        """
        http_resp = HTTP_REQUESTS.get(url)
        jsondata = http_resp.json()
        return jsondata


    def to_json(self, content):
        """
            Convert concent to json string with class parameters.
        """
        return json.dumps(content, indent=self.json_indent, sort_keys=self.json_sort)


    def update_cmd(self, arg_dict):
        """
        """
        new_keys = arg_dict.keys()
        existed_keys = self.args.keys()
        overlap = list(set(new_keys) & set(existed_keys))
        if (overlap):
            raise KeyError('Can not merge cmd args! Keys collision.')
        arg_dict.update(self.args)
