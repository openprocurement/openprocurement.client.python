# -*- coding: utf-8 -*-
from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import LOTS


class LotsClient(APIResourceClient):
    """ Client for Openregistry Lots """

    resource = LOTS

    get_lot = APIResourceClient.get_resource_item

    get_lots = APIResourceClient.get_resource_items

    patch_lot = APIResourceClient.patch_resource_item

    def patch_auction(self, lot_id, data, auction_id, access_token):
        return self.patch_resource_item_subitem(
            lot_id, {'data': data}, 'auctions', auction_id, access_token=access_token
        )
