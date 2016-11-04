import logging

from .exceptions import Conflict, Forbidden, InvalidResponse, Locked, \
    MethodNotAllowed, PreconditionFailed, ResourceGone, RequestFailed, \
    ResourceNotFound, Unauthorized, UnprocessableEntity

from munch import munchify
from requests import Session
from requests.auth import HTTPBasicAuth
from simplejson import dumps, loads

logger = logging.getLogger(__name__)
IGNORE_PARAMS = ('uri', 'path')


class APITemplateClient(object):
    """base class for API"""

    @staticmethod
    def auth(login, passwd): return HTTPBasicAuth(login, passwd)

    def __init__(self, login_pass=None, headers=None):
        self.headers = headers or {}
        self.session = Session()
        if login_pass is not None:
            self.session.auth = self.auth(*login_pass)

    def request(self, method, path=None, payload=None, json=None,
                headers=None, params_dict=None, files=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        if files:
            _headers.pop('Content-Type', None)

        response = self.session.request(
            method, path, data=payload, json=json, headers=_headers,
            params=params_dict, files=files
        )

        if response.status_code >= 400:
            if response.status_code == 404:
                raise ResourceNotFound(response)
            elif response.status_code == 401:
                raise Unauthorized(response)
            elif response.status_code == 403:
                raise Forbidden(response)
            elif response.status_code == 410:
                raise ResourceGone(response)
            elif response.status_code == 405:
                raise MethodNotAllowed(response)
            elif response.status_code == 409:
                raise Conflict(response)
            elif response.status_code == 412:
                raise PreconditionFailed(response)
            elif response.status_code == 422:
                raise UnprocessableEntity(response)
            elif response.status_code == 423:
                raise Locked(response)
            else:
                raise RequestFailed(response)

        if 'Set-Cookie' in response.headers:
            self.headers['Cookie'] = response.headers['Set-Cookie']
        return response


class APIBaseClient(APITemplateClient):
    """base class for API"""

    host_url = 'https://api-sandbox.openprocurement.org'
    api_version = '2.0'
    headers = {'Content-Type': 'application/json'}

    def __init__(self,
                 key,
                 resource,
                 host_url=None,
                 api_version=None,
                 params=None):

        super(APIBaseClient, self)\
            .__init__(login_pass=(key, ''), headers=self.headers)

        _host_url = host_url or self.host_url
        _api_version = api_version or self.api_version

        if not isinstance(params, dict):
            params = {'mode': '_all_'}
        self.params = params or {}
        # To perform some operations (e.g. create a tender)
        # we first need to obtain a cookie. For that reason,
        # here we send a HEAD request to a neutral URL.
        self.session.request('HEAD',
                             '{}/api/{}/spore'
                             .format(_host_url, _api_version))

        self.prefix_path = '{}/api/{}/{}'\
            .format(_host_url, _api_version, resource)

    def _update_params(self, params):
        for key in params:
            if key not in IGNORE_PARAMS:
                self.params[key] = params[key]

    def _create_resource_item(self, url, payload, headers=None, method='post'):
        _headers = self.headers.copy()
        _headers.update(headers or {})

        response_item = self.request(
            method, url, headers=headers, json=payload
        )
        if response_item.status_code == 201:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _get_resource_item(self, url, headers=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        response_item = self.request('GET', url, headers=_headers)
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _patch_resource_item(self, url, payload, headers=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        response_item = self.request(
            'PATCH', url, headers=_headers, payload=dumps(payload)
        )
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _upload_resource_file(
        self, url, files=None, headers=None, method='post', ds_client=None
    ):
        if ds_client:
            response = ds_client.document_upload_registered(
                files=files, headers=headers
            )

            response.update({'format': ds_client.files['mime']})
            payload = {'data': response}
            response = self._create_resource_item(
                url,
                headers=headers,
                payload=payload,
                method=method
            )
        else:
            logger.warning(
                'File upload/download/delete outside of the Document Service '
                'is deprecated'
            )
            response = self.request(
                method, url, headers=headers, files={'file': files}
            )
            if response.status_code in (201, 200):
                response = munchify(loads(response.content))
            else:
                raise InvalidResponse(response)

        return response

    def _delete_resource_item(self, url, headers=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        response_item = self.request('DELETE', url, headers=_headers)
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)
