# -*- coding: utf-8 -*-
from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import LOTS


class LotsClient(APIResourceClient):
    """ Client for Openregistry Lots """

    resource = LOTS

    get_lot = APIResourceClient.get_resource_item

    get_lots = APIResourceClient.get_resource_items

    patch_lot = APIResourceClient.patch_resource_item
