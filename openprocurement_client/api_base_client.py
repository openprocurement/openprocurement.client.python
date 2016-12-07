import logging
import uuid

from .exceptions import Conflict, Forbidden, InvalidResponse, Locked, \
    MethodNotAllowed, PreconditionFailed, ResourceGone, RequestFailed, \
    ResourceNotFound, Unauthorized, UnprocessableEntity

from functools import wraps
from io import FileIO
from munch import munchify
from os import path
from requests import Session
from requests.auth import HTTPBasicAuth
from simplejson import dumps, loads

logger = logging.getLogger(__name__)
IGNORE_PARAMS = ('uri', 'path')


def verify_file(fn):
    @wraps(fn)
    def wrapper(self, file_, *args, **kwargs):
        if isinstance(file_, basestring):
            # Using FileIO here instead of open()
            # to be able to override the filename
            # which is later used when uploading the file.
            #
            # Explanation:
            #
            # 1) requests reads the filename
            # from "name" attribute of a file-like object,
            # there is no other way to specify a filename;
            #
            # 2) The attribute may contain the full path to file,
            # which does not work well as a filename;
            #
            # 3) The attribute is readonly when using open(),
            # unlike FileIO object.
            file_ = FileIO(file_, 'rb')
            file_.name = path.basename(file_.name)
        if hasattr(file_, 'read'):
            # A file-like object must have 'read' method
            output = fn(self, file_, *args, **kwargs)
            file_.close()
            return output
        else:
            try:
                file_.close()
            except AttributeError:
                pass
            raise TypeError('Expected either a string '
                            'containing a path to file or a '
                            'file-like object, got {}'.format(type(file_)))
    return wrapper


class APITemplateClient(object):
    """base class for API"""

    @staticmethod
    def auth(login, passwd): return HTTPBasicAuth(login, passwd)

    def __init__(self, login_pass=None, headers=None, user_agent=None):
        self.headers = headers or {}
        self.session = Session()
        if login_pass is not None:
            self.session.auth = self.auth(*login_pass)

        if user_agent is None:
            self.session.headers['User-Agent'] \
                = 'op.client/{}'.format(uuid.uuid4().hex)
        else:
            self.session.headers['User-Agent'] = user_agent

    def request(self, method, path=None, payload=None, json=None,
                headers=None, params_dict=None, file_=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        if file_:
            _headers.pop('Content-Type', None)

        response = self.session.request(
            method, path, data=payload, json=json, headers=_headers,
            params=params_dict, files=file_
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
                 params=None,
                 ds_client=None,
                 user_agent=None):

        super(APIBaseClient, self)\
            .__init__(login_pass=(key, ''), headers=self.headers,
                      user_agent=user_agent)

        self.ds_client = ds_client

        _host_url = host_url or self.host_url
        _api_version = api_version or self.api_version

        if not isinstance(params, dict):
            params = {'mode': '_all_'}
        self.params = params or {}
        # To perform some operations (e.g. create a tender)
        # we first need to obtain a cookie. For that reason,
        # here we send a HEAD request to a neutral URL.
        response = self.session.request(
            'HEAD', '{}/api/{}/spore'.format(_host_url, _api_version)
        )
        response.raise_for_status()

        self.prefix_path = '{}/api/{}/{}'\
            .format(_host_url, _api_version, resource)

    @staticmethod
    def _get_access_token(obj):
        return getattr(getattr(obj, 'access', ''), 'token', '')

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
        if (response_item.status_code == 201 and method == 'post') \
                or (response_item.status_code in (200, 204)
                    and method in ('put', 'delete')):
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
        self, url, file_=None, headers=None, method='post'
    ):
        if self.ds_client:
            response = self.ds_client.document_upload_registered(
                file_=file_, headers=headers
            )

            response.update({'format': self.ds_client.files['mime']})
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
                method, url, headers=headers, file_={'file': file_}
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

    def _patch_obj_resource_item(self, patched_obj, item_obj, items_name):
        return self._patch_resource_item(
            '{}/{}/{}/{}'.format(
                self.prefix_path, patched_obj.data.id,
                items_name, item_obj['data']['id']
            ),
            payload=item_obj,
            headers={'X-Access-Token': self._get_access_token(patched_obj)}
        )

    def patch_document(self, obj, document):
        return self._patch_obj_resource_item(obj, document, 'documents')

    @verify_file
    def upload_document(self, file_, obj):
        return self._upload_resource_file(
            '{}/{}/documents'.format(
                self.prefix_path,
                obj.data.id
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(obj)}
        )

    def get_resource_item(self, id):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id))
