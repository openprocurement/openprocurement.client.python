# -*- coding: utf-8 -*-
import logging

from iso8601 import parse_date
from munch import munchify
from retrying import retry
from simplejson import loads

from openprocurement_client.constants import DOCUMENTS
from openprocurement_client.exceptions import InvalidResponse
from openprocurement_client.resources.document_service import DocumentServiceClient
from openprocurement_client.templates import APITemplateClient
from openprocurement_client.utils import verify_file


LOGGER = logging.getLogger(__name__)
IGNORE_PARAMS = ('uri', 'path')


class APIBaseClient(APITemplateClient):
    """Base class for API"""

    host_url = 'https://api-sandbox.openprocurement.org'
    api_version = '0'
    headers = {'Content-Type': 'application/json'}
    resource = ''

    def __init__(self,
                 key='',
                 resource=None,
                 host_url=None,
                 api_version=None,
                 params=None,
                 ds_config=None,
                 user_agent=None,
                 ds_client=None):

        super(APIBaseClient, self).__init__(login_pass=(key, ''),
                                            headers=self.headers,
                                            user_agent=user_agent)
        if ds_config:
            self.ds_client = DocumentServiceClient(ds_config['host_url'], ds_config['auth_ds'])
        if ds_client:
            self.ds_client = ds_client
            LOGGER.warn("Positional argument 'ds_client' is deprecated, use 'ds_config' which receive "
                        "dict with 'host_url' and 'auth_ds' keys")
        self.host_url = host_url or self.host_url
        self.api_version = api_version or self.api_version

        if not isinstance(params, dict):
            params = {'mode': '_all_'}
        self.params = params or {}
        self.resource = self.resource or resource
        self.prefix_path = '{}/api/{}/{}'.format(self.host_url, self.api_version, self.resource)
        # To perform some operations (e.g. create a tender)
        # we first need to obtain a cookie. For that reason,
        # here we send a HEAD request to a neutral URL.
        self._obtain_cookie()

    def _obtain_cookie(self):
        response = self.session.request('HEAD', self.prefix_path)
        response.raise_for_status()

    @staticmethod
    def _get_access_token(obj):
        return getattr(getattr(obj, 'access', ''), 'token', '')

    def _create_resource_item(self, url, payload, headers=None, method='POST'):
        _headers = self.headers.copy()
        _headers.update(headers or {})

        response_item = self.request(method, url, headers=_headers, json=payload)
        if ((response_item.status_code == 201 and method == 'POST') or
                (response_item.status_code in (200, 204) and method in ('PUT', 'DELETE'))):
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _delete_resource_item(self, url, headers=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        response_item = self.request('DELETE', url, headers=_headers)
        if response_item.status_code == 200:
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
        response = self.request('GET', self.prefix_path, params_dict=self.params)
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
        response_item = self.request('PATCH', url, headers=_headers, json=payload)
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    def _patch_obj_resource_item(self, patched_obj, item_obj, items_name):
        return self._patch_resource_item(
            '{}/{}/{}/{}'.format(self.prefix_path, patched_obj.data.id, items_name, item_obj['data']['id']),
            payload=item_obj,
            headers={'X-Access-Token': self._get_access_token(patched_obj)}
        )

    def patch_document(self, obj, document):
        LOGGER.warn("'patch_document is deprecated method use 'APIResourceClient.patch_document' "
                    "from 'openprocurement_client.clients' instead.")
        return self._patch_obj_resource_item(obj, document, 'documents')

    @verify_file
    def upload_document(self, file_, resource_item_id, subitem_name=DOCUMENTS, doc_type=None, use_ds_client=True,
                        doc_registration=True, depth_path=None, access_token=None):
        headers = None
        if access_token:
            headers = {'X-Access-Token': access_token}
        if isinstance(resource_item_id, dict):
            headers = {'X-Access-Token': self._get_access_token(resource_item_id)}
            resource_item_id = resource_item_id['data']['id']
        if depth_path:
            url = '{}/{}/{}/{}'.format(self.prefix_path, resource_item_id, depth_path, subitem_name)
        else:
            url = '{}/{}/{}'.format(self.prefix_path, resource_item_id, subitem_name)
        return self._upload_resource_file(url,
                                          file_=file_, headers=headers, doc_registration=doc_registration,
                                          doc_type=doc_type, use_ds_client=use_ds_client)

    def _update_params(self, params):
        for key in params:
            if key not in IGNORE_PARAMS:
                self.params[key] = params[key]

    def _upload_resource_file(self, url, file_=None, headers=None, doc_type=None, method='POST',
                              use_ds_client=True, doc_registration=True):
        if hasattr(self, 'ds_client') and use_ds_client:
            if doc_registration:
                response = self.ds_client.document_upload_registered(file_=file_, headers=headers)
            else:
                response = self.ds_client.document_upload_not_registered(file_=file_, headers=headers)
            payload = {'data': response['data']}
            if doc_type:
                payload['data']['documentType'] = doc_type
            response = self._create_resource_item(url, headers=headers, payload=payload, method=method)
        else:
            if use_ds_client:
                LOGGER.warning(
                    'use_ds_client parameter is True while DS-client is not passed to the client constructor.'
                )
            LOGGER.warning('File upload/download/delete outside of the Document Service is deprecated')
            response = self.request(method, url, headers=headers, file_={'file': file_})
            if response.status_code in (201, 200):
                response = munchify(loads(response.text))
            else:
                raise InvalidResponse(response)

        return response

    def patch_credentials(self, id, access_token):
        LOGGER.warn("'pat' method is deprecated use APIResoucreClient.pat from "
                    "from 'openprocurement_client.clients'.")
        return self._patch_resource_item('{}/{}/credentials'.format(self.prefix_path, id),
                                         payload=None,
                                         headers={'X-Access-Token': access_token})

    def renew_cookies(self):
        old_cookies = 'Old cookies:\n'
        for k in self.session.cookies.keys():
            old_cookies += '{}={}\n'.format(k, self.session.cookies[k])
        LOGGER.debug(old_cookies.strip())

        self.session.cookies.clear()

        self._obtain_cookie()

        new_cookies = 'New cookies:\n'
        for k in self.session.cookies.keys():
            new_cookies += '{}={}\n'.format(k, self.session.cookies[k])
        LOGGER.debug(new_cookies)


class APIResourceClient(APIBaseClient):
    """ API Resource Client """

    ###########################################################################
    #                        CREATE CLIENT METHODS
    ###########################################################################

    def create_resource_item(self, resource_item):
        return self._create_resource_item(self.prefix_path, resource_item)

    def create_resource_item_subitem(self, resource_item_id, subitem_obj,
                                     subitem_name, access_token=None,
                                     depth_path=None):
        headers = None
        if access_token:
            headers = {'X-Access-Token': access_token}
        if isinstance(resource_item_id, dict):
            headers = {'X-Access-Token': self._get_access_token(resource_item_id)}
            resource_item_id = resource_item_id['data']['id']
        if depth_path:
            url = '{}/{}/{}/{}'.format(self.prefix_path, resource_item_id,
                                       depth_path, subitem_name)
        else:
            url = '{}/{}/{}'.format(self.prefix_path, resource_item_id,
                                    subitem_name)
        return self._create_resource_item(url, subitem_obj, headers=headers)

    ###########################################################################
    #                        DELETE CLIENT METHODS
    ###########################################################################

    def delete_resource_item_subitem(self, resource_item_id, subitem_name,
                                     subitem_id, access_token=None,
                                     depth_path=None):
        headers = None
        if access_token:
            headers = {'X-Access-Token': access_token}
        if depth_path:
            url = '{}/{}/{}/{}/{}'.format(self.prefix_path, resource_item_id, depth_path, subitem_name, subitem_id)
        else:
            url = '{}/{}/{}/{}'.format(self.prefix_path, resource_item_id, subitem_name, subitem_id)
        return self._delete_resource_item(url, headers=headers)

    ###########################################################################
    #                          GET CLIENT METHODS
    ###########################################################################

    def get_resource_item(self, resource_item_id, headers=None):
        return self._get_resource_item(
            '{}/{}'.format(self.prefix_path, resource_item_id), headers=headers
        )

    def get_resource_item_subitem(self, resource_item_id, subitem_id_or_name,
                                  access_token=None, depth_path=None):
        headers = None
        if access_token:
            headers = {'X-Access-Token': access_token}
        if isinstance(resource_item_id, dict):
            headers = {'X-Access-Token': self._get_access_token(resource_item_id)}
            resource_item_id = resource_item_id['data']['id']
        if depth_path:
            url = '{}/{}/{}/{}'.format(self.prefix_path, resource_item_id,
                                       depth_path, subitem_id_or_name)
        else:
            url = '{}/{}/{}'.format(self.prefix_path, resource_item_id,
                                    subitem_id_or_name)
        return self._get_resource_item(url, headers=headers)

    def get_resource_items(self, params=None, feed='changes'):
        return self._get_resource_items(params=params, feed=feed)

    def get_latest_resource_items(self, date):
        iso_dt = parse_date(date)
        dt = iso_dt.strftime('%Y-%m-%d')
        tm = iso_dt.strftime('%H:%M:%S')
        data = self._get_resource_item(
            '{}?offset={}T{}&opt_fields={}_id&mode=test'.format(
                self.prefix_path,
                dt,
                tm,
                self.resource[:-1]
            )
        )
        return data

    def get_file(self, url, access_token=None):
        headers = {'X-Access-Token': access_token} if access_token else {}

        headers.update(self.headers)
        response_item = self.request('GET', url, headers=headers)

        # if response_item.status_code == 302:
        #     response_obj = request(response_item.headers['location'])
        if response_item.status_code == 200:
            return response_item.text, \
                response_item.headers['Content-Disposition'].split("; filename=")[1].strip('"')
        raise InvalidResponse(response_item)

    def get_file_properties(self, url, file_hash, access_token=None):
        headers = {'X-Access-Token': access_token} if access_token else {}
        headers.update(self.headers)
        response_item = self.request('GET', url, headers=headers)
        if response_item.status_code == 200:
            file_properties = {
                'Content_Disposition': response_item.headers['Content-Disposition'],
                'Content_Type': response_item.headers['Content-Type'],
                'url': url,
                'hash': file_hash
            }
            return file_properties
        raise InvalidResponse(response_item)

    ###########################################################################
    #                          PATCH CLIENT METHODS
    ###########################################################################

    def patch_credentials(self, resource_item_id, access_token):
        return self._patch_resource_item(
            '{}/{}/credentials'.format(self.prefix_path, resource_item_id),
            payload=None,
            headers={'X-Access-Token': access_token}
        )

    def patch_resource_item(self, resource_item_id, patch_data={}, access_token=None):
        headers = None
        if access_token:
            headers = {'X-Access-Token': access_token}
        if isinstance(resource_item_id, dict):
            headers = {'X-Access-Token': self._get_access_token(resource_item_id)}
            patch_data = {'data': resource_item_id['data']}
            resource_item_id = resource_item_id['data']['id']
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, resource_item_id),
            payload=patch_data, headers=headers
        )

    def patch_resource_item_subitem(self, resource_item_id, patch_data, subitem_name, subitem_id=None,
                                    access_token=None, depth_path=None):
        headers = None
        if access_token:
            headers = {'X-Access-Token': access_token}
        if isinstance(resource_item_id, dict):
            headers = {'X-Access-Token': self._get_access_token(resource_item_id)}
            resource_item_id = resource_item_id['data']['id']
        if not subitem_id:
            subitem_id = patch_data['data']['id']
        if depth_path:
            url = '{}/{}/{}/{}/{}'.format(
                self.prefix_path, resource_item_id, depth_path, subitem_name,
                subitem_id
            )
        else:
            url = '{}/{}/{}/{}'.format(
                self.prefix_path, resource_item_id, subitem_name, subitem_id
            )
        return self._patch_resource_item(url, patch_data, headers=headers)

    def patch_document(self, resource_item_id, document_data, document_id,
                       access_token=None, depth_path=None):
        return self.patch_resource_item_subitem(
            resource_item_id, document_data, DOCUMENTS, document_id,
            access_token, depth_path
        )

    ###########################################################################
    #                          UPLOAD CLIENT METHODS
    ###########################################################################

    @verify_file
    def update_document(self, file_, resource_item_id, document_id, subitem_name=DOCUMENTS, doc_type=None, use_ds_client=True,
                        doc_registration=True, depth_path=None, access_token=None):
        headers = None
        if access_token:
            headers = {'X-Access-Token': access_token}
        if isinstance(resource_item_id, dict):
            headers = {'X-Access-Token': self._get_access_token(resource_item_id)}
            resource_item_id = resource_item_id['data']['id']

        if depth_path:
            url = '{}/{}/{}/{}/{}'.format(self.prefix_path, resource_item_id, depth_path, subitem_name, document_id)
        else:
            url = '{}/{}/{}/{}'.format(self.prefix_path, resource_item_id, subitem_name, document_id)
        return self._upload_resource_file(url,
                                          file_=file_, headers=headers, method='PUT', use_ds_client=use_ds_client,
                                          doc_registration=doc_registration, doc_type=doc_type)

    ###########################################################################
    #                          UPLOAD CLIENT METHODS
    ###########################################################################

    def extract_credentials(self, resource_item_id):
        return self._get_resource_item('{}/{}/extract_credentials'.format(self.prefix_path, resource_item_id))

    def change_ownership(self, obj_id, transfer, access_token=None):
        try:
            self.create_resource_item_subitem(obj_id, transfer, 'ownership', access_token=access_token)
        except InvalidResponse as e:
            if e.status_code == 200:
                return munchify(loads(e.response.text))
            raise e


class APIResourceClientSync(APIResourceClient):

    def sync_resource_items(self, params=None, extra_headers=None):
        _params = (params or {}).copy()
        _params['feed'] = 'changes'
        self.headers.update(extra_headers or {})

        response = self.request('GET', self.prefix_path, params_dict=_params)
        if response.status_code == 200:
            tender_list = munchify(loads(response.text))
            return tender_list

    @retry(stop_max_attempt_number=5)
    def get_resource_item(self, resource_item_id, extra_headers=None):
        self.headers.update(extra_headers or {})
        return super(APIResourceClientSync, self).get_resource_item(resource_item_id)
