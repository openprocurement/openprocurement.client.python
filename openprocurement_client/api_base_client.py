import logging
import uuid

from .exceptions import http_exceptions_dict, InvalidResponse, RequestFailed
from .document_service_client import DocumentServiceClient

from functools import wraps
from io import FileIO
from munch import munchify
from os import path
from requests import Session
from requests.auth import HTTPBasicAuth as BasicAuth
from simplejson import loads
from retrying import retry

logger = logging.getLogger(__name__)
IGNORE_PARAMS = ('uri', 'path')


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


def verify_file(fn):
    @wraps(fn)
    def wrapper(self, file_, *args, **kwargs):
        if isinstance(file_, basestring):
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
            raise TypeError(
                'Expected either a string containing a path to file or '
                'a file-like object, got {}'.format(type(file_))
            )
    return wrapper


class APITemplateClient(object):
    """Base class template for API"""

    def __init__(self, login_pass=None, headers=None, user_agent=None):
        self.headers = headers or {}
        self.session = Session()
        if login_pass is not None:
            self.session.auth = BasicAuth(*login_pass)

        if user_agent is None:
            self.session.headers['User-Agent'] = 'op.client/{}'.format(
                uuid.uuid4().hex)
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
            raise http_exceptions_dict\
                .get(response.status_code, RequestFailed)(response)

        return response


class APIBaseClient(APITemplateClient):
    """Base class for API"""

    host_url = 'https://api-sandbox.openprocurement.org'
    api_version = '0'
    headers = {'Content-Type': 'application/json'}

    def __init__(self,
                 key='',
                 resource='tenders',
                 host_url=None,
                 api_version=None,
                 params=None,
                 ds_config=None,
                 user_agent=None):

        super(APIBaseClient, self).__init__(login_pass=(key, ''),
                                            headers=self.headers,
                                            user_agent=user_agent)
        if ds_config:
            self.ds_client = DocumentServiceClient(ds_config['host_url'],
                                                   ds_config['auth'])
        self.host_url = host_url or self.host_url
        self.api_version = api_version or self.api_version

        if not isinstance(params, dict):
            params = {'mode': '_all_'}
        self.params = params or {}
        # To perform some operations (e.g. create a tender)
        # we first need to obtain a cookie. For that reason,
        # here we send a HEAD request to a neutral URL.
        response = self.session.request(
            'HEAD', '{}/api/{}/spore'.format(self.host_url, self.api_version)
        )
        response.raise_for_status()

        self.prefix_path = '{}/api/{}/{}'.format(self.host_url,
                                                 self.api_version, resource)

    def _update_params(self, params):
        for key in params:
            if key not in IGNORE_PARAMS:
                self.params[key] = params[key]

    def _create_resource_item(self, url, payload, headers=None, method='POST'):
        _headers = self.headers.copy()
        _headers.update(headers or {})

        response_item = self.request(
            method, url, headers=_headers, json=payload
        )
        if ((response_item.status_code == 201 and method == 'POST') or
                (response_item.status_code in (200, 204) and
                 method in ('PUT', 'DELETE'))):
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _get_resource_item(self, url, headers=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        response_item = self.request('GET', url, headers=_headers)
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    @retry(stop_max_attempt_number=5)
    def _get_resource_items(self, params=None, feed='changes'):
        _params = (params or {}).copy()
        _params['feed'] = feed
        self._update_params(_params)
        response = self.request('GET',
                                self.prefix_path,
                                params_dict=self.params)
        if response.status_code == 200:
            resource_items_list = munchify(loads(response.text))
            self._update_params(resource_items_list.next_page)
            return resource_items_list.data
        elif response.status_code == 404:
            del self.params['offset']

        raise InvalidResponse(response)

    def _patch_resource_item(self, url, payload, headers=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        response_item = self.request(
            'PATCH', url, headers=_headers, json=payload
        )
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _upload_resource_file(
        self, url, file_=None, headers=None, method='POST',
        use_ds_client=True, doc_registration=True
    ):
        if use_ds_client and self.ds_client:
            if doc_registration:
                response = self.ds_client.document_upload_registered(
                    file_=file_, headers=headers
                )
            else:
                response = self.ds_client.document_upload_not_registered(
                    file_=file_, headers=headers
                )
            payload = {'data': response['data']}
            response = self._create_resource_item(
                url,
                headers=headers,
                payload=payload,
                method=method
            )
        else:
            if use_ds_client:
                logger.warning('use_ds_client parameter is True while '
                               'DS-client is not passed to the client '
                               'constructor.')
            logger.warning(
                'File upload/download/delete outside of the Document Service '
                'is deprecated'
            )
            response = self.request(
                method, url, headers=headers, file_={'file': file_}
            )
            if response.status_code in (201, 200):
                response = munchify(loads(response.text))
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
    def upload_document(self, file_, obj, use_ds_client=True,
                        doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/documents'.format(
                self.prefix_path,
                obj.data.id
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(obj)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    def get_resource_item(self, id, headers=None):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id),
                                       headers=headers)

    def patch_credentials(self, id, access_token):
        return self._patch_resource_item(
            '{}/{}/credentials'.format(self.prefix_path, id),
            payload=None,
            headers={'X-Access-Token': access_token}
        )


    def renew_cookies(self):
        old_cookies = 'Old cookies:\n'
        for k in self.session.cookies.keys():
            old_cookies += '{}={}\n'.format(k, self.session.cookies[k])
        logger.debug(old_cookies.strip())

        self.session.cookies.clear()

        response = self.session.request(
            'HEAD', '{}/api/{}/spore'.format(self.host_url, self.api_version)
        )
        response.raise_for_status()

        new_cookies = 'New cookies:\n'
        for k in self.session.cookies.keys():
            new_cookies += '{}={}\n'.format(k, self.session.cookies[k])
        logger.debug(new_cookies)

    def create_resource_item(self, resource_item):
        return self._create_resource_item(self.prefix_path, resource_item)

    def patch_resource_item(self, resource_item):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, resource_item['data']['id']),
            payload=resource_item,
            headers={'X-Access-Token': self._get_access_token(resource_item)}
        )
