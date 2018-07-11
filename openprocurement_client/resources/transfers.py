# -*- coding: utf-8 -*-
from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import TRANSFERS


class TransfersClient(APIResourceClient):
    """ Client for OpenProcurement Transfers """

    resource = TRANSFERS

    get_transfer = APIResourceClient.get_resource_item

    create_transfer = APIResourceClient.create_resource_item

    patch_transfer = APIResourceClient.patch_resource_item
