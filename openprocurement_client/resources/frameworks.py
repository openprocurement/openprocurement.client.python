# -*- coding: utf-8 -*-
import logging
from retrying import retry

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import (FRAMEWORKS, DOCUMENTS)

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

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################


    ###########################################################################
    #             UPLOAD FILE API METHODS
    ###########################################################################
    def upload_framework_document(self, file, framework_id, use_ds_client=True,
                              doc_registration=True, access_token=None):
        depth_path = '{}'.format(DOCUMENTS)
        return self.upload_document(file, framework_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)