# -*- coding: utf-8 -*-
from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import LOTS


class LotsClient(APIResourceClient):
    """ Client for Openregistry Lots """

    resource = LOTS

    def __init__(self, *args, **kwargs):
        super(LotsClient, self).__init__(resource=self.resource, *args,
                                         **kwargs)

    get_lot = APIResourceClient.get_resource_item

    get_lots = APIResourceClient.get_resource_items
