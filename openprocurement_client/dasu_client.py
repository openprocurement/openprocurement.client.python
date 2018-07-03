import logging

from .api_base_client import APIBaseClient, APITemplateClient, verify_file
from .exceptions import InvalidResponse

from iso8601 import parse_date
from munch import munchify
from retrying import retry
from simplejson import loads


logger = logging.getLogger(__name__)

IGNORE_PARAMS = ('uri', 'path')


class APIClient(APIBaseClient):

    host_url = 'https://audit-api-sandbox.prozorro.gov.ua'
    api_version = '2.4'
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
        self.host_url = host_url or self.host_url
        self.api_version = api_version or self.api_version

        if not isinstance(params, dict):
            params = {'mode': '_all_'}
        self.params = params or {}
        response = self.session.request(
            'HEAD', '{}/api/{}/{}'\
            .format(self.host_url, self.api_version, resource)
        )
        response.raise_for_status()

        self.prefix_path = '{}/api/{}/{}'\
            .format(self.host_url, self.api_version, resource)


class DasuClient(APIClient):
    """client for monitorings"""

    def __init__(self,
                 key,
                 resource='monitorings',  # another possible value is 'auctions'
                 host_url=None,
                 api_version=None,
                 params=None,
                 ds_client=None,
                 user_agent=None):
        super(DasuClient, self).__init__(
            key, resource, host_url, api_version, params, ds_client,
            user_agent
        )

    @retry(stop_max_attempt_number=5)
    def get_monitorings(self, params=None, feed='changes'):
        _params = (params or {}).copy()
        _params['feed'] = feed
        self._update_params(_params)
        response = self.request('GET',
                                self.prefix_path,
                                params_dict=self.params)
        if response.status_code == 200:
            tender_list = munchify(loads(response.text))
            self._update_params(tender_list.next_page)
            return tender_list.data
        elif response.status_code == 404:
            del self.params['offset']

        raise InvalidResponse(response)

    def get_latest_monitorings(self, date, monitoring_id):
        iso_dt = parse_date(date)
        dt = iso_dt.strftime('%Y-%m-%d')
        tm = iso_dt.strftime('%H:%M:%S')
        data = self._get_resource_item(
            '{}?offset={}T{}&opt_fields=monitoring_id&mode=test'.format(
                self.prefix_path,
                dt,
                tm
            )
        )
        return data

    def _get_monitoring_resource_list(self, monitoring, items_name):
        return self._get_resource_item(
            '{}/{}/{}'.format(self.prefix_path, tender.data.id, items_name),
            headers={'X-Access-Token': self._get_access_token(monitoring)}
        )

    def _create_monitoring_resource_item(self, monitoring, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, monitoring.data.id, items_name),
            item_obj,
            headers={'X-Access-Token': self._get_access_token(monitoring)}
        )

    def create_monitoring(self, monitoring):
        return self._create_resource_item(self.prefix_path, monitoring)

    def _create_monitoring_resource_item(self, monitoring, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, monitoring.data.id, items_name),
            item_obj,
            headers={'X-Access-Token': self._get_access_token(monitoring)}
        )

    def get_monitoring(self, id, access_token=None):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id), headers={'X-Access-Token':access_token})

    def patch_credentials(self, token, id):
        return self._patch_resource_item(
            '{}/{}/{}'.format(self.prefix_path, id, 'credentials'),
            payload='', 
            headers={'X-Access-Token': token}
        )

    def patch_monitoring(self, monitoring, id):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, id),
            payload=monitoring,
            headers={'X-Access-Token': self._get_access_token(monitoring)}
        )

    def patch_monitoring_obj(self, patched_obj, item_obj, items_name, item_id=None):
        return self._patch_resource_item(
            '{}/{}/{}/{}'.format(
                self.prefix_path, patched_obj.data.id,
                items_name, item_id
            ),
            payload=item_obj,
            headers={'X-Access-Token': self._get_access_token(patched_obj)}
        )
    
    def patch_dialogue(self, monitoring, dialogue, dialogue_id):
        return self.patch_monitoring_obj(monitoring, dialogue, 'dialogues', dialogue_id)

    def create_dialogue(self, monitoring, dialogue):
       return self._create_monitoring_resource_item(monitoring, dialogue, 'dialogues')

    def create_party(self, monitoring, party):
        return self._create_monitoring_resource_item(monitoring, party, 'parties')

    def patch_eliminationReport(self, monitoring, report):
        return self._create_resource_item(
            '{}/{}/{}'.format(
                self.prefix_path, monitoring.data.id,
                'eliminationReport'
            ),
            payload=report,
            headers={'X-Access-Token': self._get_access_token(monitoring)},
            method='PUT'
        )

    def patch_appeal(self, monitoring, appeal):
        return self._create_resource_item(
            '{}/{}/{}'.format(
                self.prefix_path, monitoring.data.id,
                'appeal'
            ),
            payload=appeal,
            headers={'X-Access-Token': self._get_access_token(monitoring)},
            method='PUT'
        )

    @verify_file
    def upload_monitoring_document(self, file_, monitoring, obj, use_ds_client=True,
                        doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/{}/documents'.format(
                self.prefix_path,
                monitoring.data.id,
                obj
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(monitoring)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def upload_obj_document(self, file_, obj, use_ds_client=True,
                        doc_registration=True):
        response = self.ds_client.document_upload_registered(
            file_=file_, 
            headers={'X-Access-Token': self._get_access_token(obj)}
        )
        return munchify(response)
