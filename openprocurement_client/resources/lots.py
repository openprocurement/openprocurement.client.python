# -*- coding: utf-8 -*-
from retrying import retry

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import LOTS
from openprocurement_client.exceptions import RequestFailed


class LotsClient(APIResourceClient):
    """ Client for Openregistry Lots """

    resource = LOTS

    def __init__(self, *args, **kwargs):
        super(LotsClient, self).__init__(resource=self.resource, *args,
                                         **kwargs)

    get_lots = APIResourceClient.get_resource_items

    @retry(wait_exponential_multiplier=200,
           wait_exponential_max=1200,
           stop_max_delay=45000,
           retry_on_exception=lambda exc: isinstance(exc, RequestFailed))
    def patch_lot(self, lot_id, patch_data):
        return self.patch_resource_item(lot_id, patch_data)

    @retry(wait_exponential_multiplier=200,
           wait_exponential_max=1200,
           stop_max_delay=45000,
           retry_on_exception=lambda exc: isinstance(exc, RequestFailed))
    def get_lot(self, lot_id):
        return self.get_resource_item(lot_id)
