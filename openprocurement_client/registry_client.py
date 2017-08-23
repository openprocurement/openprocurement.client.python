import logging

from .client import APIClient
from .exceptions import InvalidResponse

from iso8601 import parse_date
from munch import munchify
from retrying import retry
from simplejson import loads


class LotsClient(APIClient):
    """ Client for Openregistry Lots """

    api_version = '0.1'
    resource = 'lots'

    def __init__(self, *args, **kwargs):
        super(LotsClient, self).__init__(resource=self.resource, *args,
                                         **kwargs)

    def get_lot(self, lot_id, headers=None):
        return self.get_resource_item(lot_id, headers=headers)

    def get_lots(self, params=None, feed='changes'):
        return self._get_resource_items(params=params, feed=feed)


class AssetsClient(APIBaseClient):
    """ Client for Openregistry Assets """

    api_version = '0.1'
    resource = 'assets'

    def __init__(self, *args, **kwargs):
        super(AssetsClient, self).__init__(resource=self.resource, *args,
                                           **kwargs)

    def get_asset(self, asset_id, headers=None):
        return self.get_resource_item(asset_id, headers=headers)

    def get_assets(self, params=None, feed='changes'):
        return self._get_resource_items(params=params, feed=feed)
