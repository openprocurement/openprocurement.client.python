# -*- coding: utf-8 -*-
from zope.deprecation import deprecation

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import (
   AGREEMENTS,
   CHANGES,
   DOCUMENTS,
)


class AgreementClient(APIResourceClient):
    """ Client for agreements """
    resource = AGREEMENTS

    def get_agreement(self, agreement_id):
        return self.get_resource_item(agreement_id)

    def get_agreements(self, params=None, feed=CHANGES):
        return self.get_resource_items(params=params, feed=feed)

    def create_change(self, agreement_id, change_data, access_token=None):
        return self.create_resource_item_subitem(
            agreement_id, change_data, CHANGES, access_token=access_token)

    def patch_agreement(self, agreement_id, data, access_token=None):
        return self.patch_resource_item(agreement_id, data, access_token=access_token)

    def patch_change(self, agreement_id, data, change_id, access_token=None):
        return self.patch_resource_item_subitem(
            agreement_id, data, CHANGES, change_id, access_token=access_token)

    def patch_document(self, agreement_id, data, document_id, access_token=None):
        return self.patch_resource_item_subitem(
            agreement_id, data, DOCUMENTS, document_id, access_token=access_token)