# -*- coding: utf-8 -*-
from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import ASSETS


class AssetsClient(APIResourceClient):
    """ Client for Openregistry Assets """

    resource = ASSETS

    def __init__(self, *args, **kwargs):
        super(AssetsClient, self).__init__(resource=self.resource, *args,
                                           **kwargs)

    get_asset = APIResourceClient.get_resource_item

    get_assets = APIResourceClient.get_resource_items

    patch_asset = APIResourceClient.patch_resource_item
