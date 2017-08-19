import logging

from .api_base_client import APIBaseClient, APITemplateClient, verify_file
from .exceptions import InvalidResponse

from iso8601 import parse_date
from munch import munchify
from retrying import retry
from simplejson import loads


class RegistryClient(APIBaseClient):
    """ Client for validate members by EDR """

    host_url = 'https://192.168.50.9'
    api_version = '0.1'

    def __init__(self,
                 key,
                 resource='lots',  # another possible value is 'assets'
                 host_url=None,
                 api_version=None,
                 params=None,
                 ds_client=None,
                 user_agent=None):
        super(RegistryClient, self).__init__(
            key, resource, host_url, api_version, params, ds_client,
            user_agent
        )
        self.host_url = host_url or self.host_url
        self.api_version = api_version or self.api_version

    def create_asset(self, asset):
        return self._create_resource_item(self.prefix_path, asset)

    def create_lot(self, lot):
        return self._create_resource_item(self.prefix_path, lot)

    def get_assets(self, extra_headers=None):
        self.headers.update(extra_headers or {})
        response = self.request(
            'GET',
            '{}/api/{}/assets'.format(self.host_url, self.api_version)
        )
        return process_response(response)

    def get_lots(self, extra_headers=None):
        resp = self.request('GET', 'http://localhost:20602/api/0.10/lots')

        self.headers.update(extra_headers or {})
        response = self.request(
            'GET',
            '{}/api/{}/lots'.format(self.host_url, self.api_version)
        )
        return process_response(response)

    def get_asset(self, asset_id=None, extra_headers=None):
        self.headers.update(extra_headers or {})

        response = self.request(
            'GET',
            '{}/api/{}/assets/{}'.format(self.host_url, self.api_version, asset_id)
        )
        return process_response(response)

    def get_lot(self, lot_id=None, extra_headers=None):
        self.headers.update(extra_headers or {})

        response = self.request(
            'GET',
            '{}/api/{}/lots/{}'.format(self.host_url, self.api_version, lot_id)
        )
        return process_response(response)

    def patch_asset(self, asset):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, asset['data']['id']),
            payload=asset,
            headers={'X-Access-Token': self._get_access_token(asset)}
        )

    def patch_lot(self, lot):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, lot['data']['id']),
            payload=lot,
            headers={'X-Access-Token': self._get_access_token(lot)}
        )


class RegistryClientSync(RegistryClient):
    def sync_item(self, params=None, extra_headers=None):
        _params = (params or {}).copy()
        _params['feed'] = 'changes'
        self.headers.update(extra_headers or {})

        response = self.request('GET', self.prefix_path,
                                params_dict=_params)
        if response.status_code == 200:
            item_list = munchify(loads(response.text))
            return item_list

    @retry(stop_max_attempt_number=5)
    def get_lot_by_id(self, id, extra_headers=None):
        self.headers.update(extra_headers or {})
        return super(RegistryClientSync, self).get_lot(id)

    @retry(stop_max_attempt_number=5)
    def get_asset_by_id(self, id, extra_headers=None):
        self.headers.update(extra_headers or {})
        return super(RegistryClientSync, self).get_asset(id)


def process_response(response):
    if response.status_code == 200:
        return munchify(loads(response.text))
    raise InvalidResponse(response)
