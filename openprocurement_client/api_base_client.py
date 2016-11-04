from .exceptions import Conflict, Forbidden, InvalidResponse, Locked, \
    MethodNotAllowed, PreconditionFailed, ResourceGone, RequestFailed, \
    ResourceNotFound, Unauthorized, UnprocessableEntity

from munch import munchify
from requests import Session
from requests.auth import HTTPBasicAuth
from simplejson import dumps, loads


IGNORE_PARAMS = ('uri', 'path')


class APITemplateClient(object):
    """base class for API"""

    @staticmethod
    def auth(login, passwd): return HTTPBasicAuth(login, passwd)

    def __init__(self, host_url, api_version,
                 resource, auth=None, params=None):

        self.session = Session()
        if auth:
            self.session.auth = auth

        self.host_url = host_url
        self.prefix_path = '{}/api/{}/{}'\
            .format(host_url, api_version, resource)
        if not isinstance(params, dict):
            params = {'mode': '_all_'}
        self.params = params
        self.headers = {'Content-Type': 'application/json'}
        # To perform some operations (e.g. create a tender)
        # we first need to obtain a cookie. For that reason,
        # here we send a HEAD request to a neutral URL.
        self.session\
            .request('HEAD', '{}/api/{}/spore'.format(host_url, api_version))

    def request(self, method, path=None, payload=None, json=None,
                headers=None, params_dict=None, files=None):
        _headers = dict(self.headers)
        _headers.update(headers or {})
        if files:
            del _headers['Content-Type']

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

    def __init__(self, key, host_url, api_version,
                 resource, params=None, ds_client=None):

        # it should be placed here.
        from .document_service_client import DocumentServiceClient

        super(APIBaseClient, self).__init__(host_url,
                                            api_version,
                                            resource,
                                            auth=self.auth(key, ''),
                                            params=params)

        self.ds_client \
            = ds_client or DocumentServiceClient(api_version, resource)

    def _update_params(self, params):
        for key in params:
            if key not in IGNORE_PARAMS:
                self.params[key] = params[key]

    def _create_resource_item(self, url, payload, headers={}):
        headers.update(self.headers)
        response_item = self.request(
            'POST', url, headers=headers, payload=dumps(payload)
        )
        if response_item.status_code == 201:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _get_resource_item(self, url, headers={}):
        headers.update(self.headers)
        response_item = self.request('GET', url, headers=headers)
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _patch_resource_item(self, url, payload, headers={}):
        headers.update(self.headers)
        response_item = self.request(
            'PATCH', url, headers=headers, payload=dumps(payload)
        )
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _add_document_in_api(self, url, payload, headers={}):
        response_item = self.request(
            'POST', url, headers=headers, json=payload
        )
        if response_item.status_code != 201:
            raise InvalidResponse(response_item)

        return munchify(loads(response_item.content))

    def _upload_resource_file(self, url, files=None, headers={}):
        file_headers = dict(self.headers)
        file_headers.update(headers)

        self.ds_client.files = self.ds_client.files_processing(files)

        file_name = self.ds_client.files['file_payload']['file'][0]
        md5 = self.ds_client.files['md5']

        response = self.ds_client.register_document_upload(
            payload={'data': {'hash': md5}},
            headers=headers
        )
        url_upload = response.upload_url

        payload = {
            "data": {
                "url": response['data']['url'],
                "title": file_name,
                "hash": md5,
                "format": self.ds_client.files['mime']
            }
        }
        self._add_document_in_api(
            url,
            headers=headers,
            payload=payload
        )

        response = self.ds_client.document_upload(
            url=url_upload,
            headers=headers
        )

        return response

    def _delete_resource_item(self, url, headers={}):
        response_item = self.request('DELETE', url, headers=headers)
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)
