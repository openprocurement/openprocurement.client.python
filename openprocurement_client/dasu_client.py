import logging

from .api_base_client import APIBaseClient, APITemplateClient, verify_file
from .exceptions import InvalidResponse

from munch import munchify
from retrying import retry
from simplejson import loads


logger = logging.getLogger(__name__)

IGNORE_PARAMS = ('uri', 'path')


class DasuClient(APIBaseClient, APITemplateClient):
    """client for monitorings"""

    host_url = 'https://audit-api-sandbox.prozorro.gov.ua'
    api_version = '2.4'
    headers = {'Content-Type': 'application/json'}

    def __init__(self,
                 key,
                 resource='monitorings',
                 host_url=None,
                 api_version=None,
                 params=None,
                 ds_client=None,
                 user_agent=None):

        APITemplateClient.__init__(self, login_pass=(key, ''), headers=self.headers,
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

    @retry(stop_max_attempt_number=5)
    def get_monitorings(self, params=None, feed='changes'):
        _params = (params or {}).copy()
        _params['feed'] = feed
        self._update_params(_params)
        response = self.request('GET',
                                self.prefix_path,
                                params_dict=self.params)
        if response.status_code == 200:
            monitoring_list = munchify(loads(response.text))
            self._update_params(monitoring_list.next_page)
            return monitoring_list.data
        elif response.status_code == 404:
            del self.params['offset']

        raise InvalidResponse(response)

    def get_monitoring(self, monitoring_id, access_token=None):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, monitoring_id),
            headers={'X-Access-Token':access_token}
        )

    def create_monitoring(self, monitoring):
        return self._create_resource_item(self.prefix_path, monitoring)

    def create_post(self, monitoring, dialogue):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, monitoring.data.id, 'posts'),
            dialogue,
            headers={'X-Access-Token': self._get_access_token(monitoring)}
        )

    def create_party(self, monitoring, party):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, monitoring.data.id, 'parties'),
            party,
            headers={'X-Access-Token': self._get_access_token(monitoring)}
        )

    def patch_monitoring(self, monitoring, monitoring_id):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, monitoring_id),
            payload=monitoring,
            headers={'X-Access-Token': self._get_access_token(monitoring)}
        )

    def patch_post(self, monitoring, dialogue, dialogue_id):
        return self._patch_resource_item(
            '{}/{}/{}/{}'.format(
                self.prefix_path, monitoring.data.id,
                'posts', dialogue_id
            ),
            payload=dialogue,
            headers={'X-Access-Token': self._get_access_token(monitoring)}
        )

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
    def upload_obj_document(self, file_, obj, use_ds_client=True,
                            doc_registration=True):
        response = self.ds_client.document_upload_registered(
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(obj)}
        )
        return munchify(response)