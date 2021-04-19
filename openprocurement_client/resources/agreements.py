# -*- coding: utf-8 -*-
from zope.deprecation import deprecation
from simplejson import loads

from openprocurement_client.compatibility_utils import munchify_factory
from openprocurement_client.exceptions import InvalidResponse
from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import (
   AGREEMENTS,
   CHANGES,
   DOCUMENTS,
)

munchify = munchify_factory()


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

    def find_agreements_by_classification_ids(self, classification_id, additional_classifications=""):
        url = "{}_by_classification/{}".format(self.prefix_path, classification_id)
        params = {}
        if additional_classifications:
            params["additional_classifications"] = additional_classifications.join(",")
        response = self.request('GET', url, params_dict=params)
        if response.status_code == 200:
            resource_items_list = munchify(loads(response.text))
            self._update_params(resource_items_list.next_page)
            return resource_items_list.data
        elif response.status_code == 404:
            del self.params['offset']

        raise InvalidResponse(response)
