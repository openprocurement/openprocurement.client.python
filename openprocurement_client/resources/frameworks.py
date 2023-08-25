# -*- coding: utf-8 -*-
import logging
from retrying import retry

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import (FRAMEWORKS, DOCUMENTS, SUBMISSIONS, QUALIFICATIONS)

LOGGER = logging.getLogger(__name__)


class FrameworksClient(APIResourceClient):
    """Client for frameworks"""

    resource = FRAMEWORKS

    ###########################################################################
    #             GET ITEMS LIST API METHODS
    ###########################################################################

    retry(stop_max_attempt_number=5)
    def get_qualifications(self, params=None, feed='changes'):
        return self.get_resource_items(params=params, feed=feed)

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################

    def create_qualification(self, framework):
        return self.create_resource_item(framework)

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_qualification(self, framework_id):
        return self.get_resource_item(framework_id)

    def get_documents(self, framework_id, access_token=None):
        return self.get_resource_item_subitem(framework_id, DOCUMENTS, access_token=access_token)

    def get_submissions(self, framework_id, access_token=None):
        return self.get_resource_item_subitem(framework_id, SUBMISSIONS, access_token=access_token)

    def get_qualifications(self, framework_id, access_token=None):
        return self.get_resource_item_subitem(framework_id, QUALIFICATIONS, access_token=access_token)

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################
    def patch_framework(self, framework_id, patch_data={}, access_token=None):
        return self.patch_resource_item(framework_id, patch_data, access_token=access_token)

    ###########################################################################
    #             UPLOAD FILE API METHODS
    ###########################################################################
    def upload_framework_document(self, file, framework_id, use_ds_client=True,
                              doc_registration=True, access_token=None):
        return self.upload_document(file, framework_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    access_token=access_token)