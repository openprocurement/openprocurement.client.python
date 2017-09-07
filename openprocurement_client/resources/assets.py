# -*- coding: utf-8 -*-
from retrying import retry

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import ASSETS
from openprocurement_client.exceptions import RequestFailed


class AssetsClient(APIResourceClient):
    """ Client for Openregistry Assets """

    resource = ASSETS

    def __init__(self, *args, **kwargs):
        super(AssetsClient, self).__init__(resource=self.resource, *args,
                                           **kwargs)

    get_assets = APIResourceClient.get_resource_items

    @retry(wait_exponential_multiplier=200,
           wait_exponential_max=1200,
           stop_max_delay=45000,
           retry_on_exception=lambda exc: isinstance(exc, RequestFailed))
    def patch_asset(self, asset_id, patch_data):
        return self.patch_resource_item(asset_id, patch_data)

    @retry(wait_exponential_multiplier=200,
           wait_exponential_max=1200,
           stop_max_delay=45000,
           retry_on_exception=lambda exc: isinstance(exc, RequestFailed))
    def get_asset(self, asset_id):
        return self.get_resource_item(asset_id)
