# -*- coding: utf-8 -*-
import logging
from retrying import retry

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import FRAMEWORKS

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

    def create_qualification(self, qualification):
        return self.create_resource_item(qualification)

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_qualification(self, qualification_id):
        return self.get_resource_item(qualification_id)

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################
