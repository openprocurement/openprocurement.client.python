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

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################

    def create_qualification(self, qualification):
        return self.create_resource_item(qualification)

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################
