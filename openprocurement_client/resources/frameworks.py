# -*- coding: utf-8 -*-
import logging
from retrying import retry

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import (FRAMEWORKS, DOCUMENTS, SUBMISSION)
from openprocurement_client.exceptions import InvalidResponse

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
    def create_submission(self, submission):
        submission_resource= SUBMISSION
        url = self.host_url.replace(self.resource, submission_resource)
        response_item = self.request('POST', url, headers=self.headers, json=submission)
        if response_item.status_code in (200, 201):
            return self.munchify(self.loads(response_item.text))
        raise InvalidResponse(response_item)

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_qualification(self, framework_id):
        return self.get_resource_item(framework_id)

    def get_documents(self, framework_id, access_token=None):
        return self.get_resource_item_subitem(framework_id, DOCUMENTS, access_token=access_token)

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