#/usr/bin/python3
"""
 This is a Base class for the tmcmd scripts and should be used Only for inheritance.
The main purpose of this class is to provide mechanism of handling HTTP requests,
such as get, post, delete and etc.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


import json
import os
import requests as HTTP_REQUESTS

from pdb import set_trace

from werkzeug.datastructures import FileStorage

def _NST(func):     # No Stack Trace
    def new_func(*args, **kwargs):
        self = args[0]
        try:
            ret = func(*args, **kwargs)
            return ret
        except HTTP_REQUESTS.exceptions.ConnectionError as e:
            raise RuntimeError('No server at %s' % self.url)
        except Exception as e:
            print('%s failed: %s' % (func.__name__, str(e)))

    # Be a well-behaved decorator
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


class TmCmd():

    # Strangle a rookie today.
    args = {}

    def __init__(self, sort=True, headers=None, indent=4, **options):
        if headers is None:
            self.header = {'Accept' : 'application/json; version=1.0'}
        else:
            self.header = headers

        self.server = options.get('server', 'localhost')
        self.port = options.get('port', '31178')
        #default_base_url = '%s:%s' % (server, port)
        # Note: os ENV prioritiez over command line port and server
        #self.url = 'http://%s/manifesting/api/' % os.getenv(
        #    'TM_MANIFEST_SERVERPORT', default_base_url)

        self.json_indent = indent
        self.json_sort = sort
        self.show_name = None
        self.verbose = options.get('verbose', False)


    @property
    def url(self):
        ''' Build endpoint base url using self.server and self.port values.
        NOTE: Server and Port a always overwritten by TM_MANIFEST_SERVERPORT OS
        environment variable (if it is set).
        '''
        default_base_url = '%s:%s' % (self.server, self.port)
        return 'http://%s/manifesting/api/' % os.getenv(
            'TM_MANIFEST_SERVERPORT', default_base_url)



    @_NST
    def listall(self, arg_list=None, **options):
        """
            Intended to be overridden by inherited class.
        """
        self.server = options.get('server', self.server)
        self.port = options.get('port', self.port)

        if arg_list is None:
            arg_list = []
        assert len(arg_list) == 0, 'This function does not take non-optional arguments!'
        if 'verbose' in options and options['verbose']:
            print(' - Sending request to "%s"...' % self.url)


    def show(self, target, **options):
        """
            Intended to be overridden by inherited class.
        """
        self.server = options.get('server', self.server)
        self.port = options.get('port', self.port)

        assert len(target) >= 1, 'Missing argument: thisfunction <name>!'
        # Let user pass both types to avoid confusion passing args as "list"
        # for a single argument.  Passing list is helpful for a generic
        # function call, (as in tm_manifest.py)
        self.show_name = target[0] if isinstance(target, list) else target
        if 'verbose' in options and options['verbose']:
            print(' - Sending request to "%s"...' % self.url)


    def delete(self, target, **options):
        """
            Base class to handle delete routines.
        """
        self.server = options.get('server', self.server)
        self.port = options.get('port', self.port)

        assert len(target) >= 1, 'Missing argument: delete <name>!'
        self.show_name = target[0] if isinstance(target, list) else target
        if options.get('verbose', False):
            print(' - Sending request to delete %s' % (self.url, target[0]))


    @_NST
    def http_request(self, url, **options):
        """
            Do a http request on the provided url and return a response
        in jsong format (if abailable).
        :param 'url': [str] url request.
        :param 'options[payload]': [dict]
        :return: [json]
        """
        headers = options.get('headers', self.header)
        if options.get('payload', False):
            http_resp = HTTP_REQUESTS.put(
                url, options['payload'], headers=headers)
        else:
            http_resp = HTTP_REQUESTS.get(url, headers=headers)
        return http_resp

    @_NST
    def http_download(self, url, destination, **options):
        """
            Do a download http request on the provided url that is pointing
        to a file.  Save the file to the requested destination.
        :param 'url': [str] url link to a file to download.
        :param 'destination': [str] destination to save downloaded file to.
        :return: None
        """
        headers = options.get('headers', self.header)
        downloaded = HTTP_REQUESTS.get(url, stream=True, headers=headers)
        with open(destination, "wb") as dest_file:
            # need to feedback a download bar to the screen here.
            dest_file.write(downloaded.content)

    @_NST
    def http_upload(self, url, **kwargs):
        """
            Upload a file to a destination url.

        :param 'url': [str] url link to a destination to upload a file.
        :param 'file_path': [str] path to a file to upload on the local system.
        :param 'kwargs': [dict] additional parameters:
                        :header: [str] HTTP request header string.
        """
        headers = kwargs.get('headers', self.header)
        payload = kwargs.get('payload', {})
        files = payload.get('files', None)
        upload = HTTP_REQUESTS.post(
            url, headers=headers, data=json.dumps(payload) )
        return upload

    @_NST
    def http_delete(self, url, **kwargs):
        """
            Make an HTTP Delete request to delte a target on the server.

        :param 'url': [str] url link to a destination to upload a file.
        :param 'file_path': [str] path to a file to upload on the local system.
        :param 'kwargs': [dict] additional parameters:
                        :header: [str] HTTP request header string.
        """
        headers = kwargs.get('headers', self.header)
        payload = kwargs.get('payload', {})
        delete = HTTP_REQUESTS.delete(url, headers=headers)
        return delete

    def to_json(self, content):
        """
            Convert content to JSON string with class parameters.
        """
        try:
            if isinstance(content, HTTP_REQUESTS.models.Response):
                response_text = json.loads(content.text)
                response_code = str(content.status_code)
                return json.dumps(
                    {response_code: response_text},
                    indent=self.json_indent, sort_keys=self.json_sort)
            else:
                return json.dumps(
                    content, indent=self.json_indent, sort_keys=self.json_sort)
        except (ValueError, TypeError) as err:
            if self.verbose:
                return '{ "error" : %s }' % (err)

        response = { content.status_code : content.text }
        return json.dumps(response)

    def update_cmd(self, arg_dict):
        """
            Add "doc string" of each function defined in a TmCmd subclass.
        """
        new_keys = arg_dict.keys()
        existed_keys = self.args.keys()
        overlap = list(set(new_keys) & set(existed_keys))
        if (overlap):
            raise KeyError('Can not merge cmd args! Keys collision.')
        arg_dict.update(self.args)
