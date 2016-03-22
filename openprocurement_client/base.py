import logging

from functools import wraps
from munch import munchify
from restkit import BasicAuth, request, Resource
from simplejson import dumps, loads

from openprocurement_client.exceptions import InvalidResponse, ResourceNotFound

logger = logging.getLogger(__name__)

IGNORE_PARAMS = ('uri', 'path')


def verify_file(fn):
    @wraps(fn)
    def wrapper(self, file_, *args, **kwargs):
        if isinstance(file_, str):
            file_ = open(file_, 'rb')
        if hasattr(file_, 'read'):
            # A file-like object must have 'read' method
            return fn(self, file_, *args, **kwargs)
        else:
            raise TypeError('Expected either a string '
                            'containing a path to file or a '
                            'file-like object, got {}'.format(type(file_)))
    return wrapper


class APIBaseClient(Resource):
    """base class for API"""
    def __init__(self, key,
                 host_url,
                 api_version,
                 resource,
                 params=None,
                 **kwargs):
        super(APIBaseClient, self).__init__(
            host_url,
            filters=[BasicAuth(key, "")],
            **kwargs
        )
        self.prefix_path = '/api/{}/{}'.format(api_version, resource)
        if not isinstance(params, dict):
            params = {"mode": "_all_"}
        self.params = params
        self.headers = {"Content-Type": "application/json"}
        # To perform some operations (e.g. create a tender)
        # we first need to obtain a cookie. For that reason,
        # here we send a HEAD request to a neutral URL.
        self.head('/api/{}/spore'.format(api_version))

    def request(self, method, path=None, payload=None, headers=None,
                params_dict=None, **params):
        _headers = dict(self.headers)
        _headers.update(headers or {})
        try:
            response = super(APIBaseClient, self).request(
                method, path=path, payload=payload, headers=_headers,
                params_dict=params_dict, **params
            )
            if 'Set-Cookie' in response.headers:
                self.headers['Cookie'] = response.headers['Set-Cookie']
            return response
        except ResourceNotFound as e:
            if 'Set-Cookie' in e.response.headers:
                self.headers['Cookie'] = e.response.headers['Set-Cookie']
            raise e

    def patch(self, path=None, payload=None, headers=None,
              params_dict=None, **params):
        """ HTTP PATCH

        - payload: string passed to the body of the request
        - path: string  additionnal path to the uri
        - headers: dict, optionnal headers that will
            be added to HTTP request.
        - params: Optionnal parameterss added to the request
        """

        return self.request("PATCH", path=path, payload=payload,
                            headers=headers, params_dict=params_dict, **params)

    def delete(self, path=None, headers=None):
        """ HTTP DELETE
        - path: string  additionnal path to the uri
        - headers: dict, optionnal headers that will
            be added to HTTP request.
        - params: Optionnal parameterss added to the request
        """
        return self.request("DELETE", path=path, headers=headers)

    def _update_params(self, params):
        for key in params:
            if key not in IGNORE_PARAMS:
                self.params[key] = params[key]

    def _create_resource_item(self, url, payload, headers={}):
        headers.update(self.headers)
        response_item = self.post(
            url, headers=headers, payload=dumps(payload)
        )
        if response_item.status_int == 201:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def _get_resource_item(self, url, headers={}):
        headers.update(self.headers)
        response_item = self.get(url, headers=headers)
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def _patch_resource_item(self, url, payload, headers={}):
        headers.update(self.headers)
        response_item = self.patch(
            url, headers=headers, payload=dumps(payload)
        )
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def _upload_resource_file(self, url, data, headers={}, method='post'):
        file_headers = {}
        file_headers.update(self.headers)
        file_headers.update(headers)
        file_headers['Content-Type'] = "multipart/form-data"
        response_item = getattr(self, method)(
            url, headers=file_headers, payload=data
        )
        if response_item.status_int in (201, 200):
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def _delete_resource_item(self, url, headers={}):
        response_item = self.delete(url, headers=headers)
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse