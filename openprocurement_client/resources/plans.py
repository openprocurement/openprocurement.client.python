# -*- coding: utf-8 -*-
import logging

from zope.deprecation import deprecation

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import CHANGES, PLANS


LOGGER = logging.getLogger(__name__)


class PlansClient(APIResourceClient):
    """Client for plans"""

    api_version = '0'
    resource = PLANS

    ###########################################################################
    #             GET ITEMS LIST API METHODS
    ###########################################################################

    def get_plans(self, params=None, feed=CHANGES):
        return self.get_resource_items(params, feed)

    def get_latest_plans(self, date):
        return self.get_latest_resource_items(date)

    @deprecation.deprecate("use get_resource_item_subitem")
    def _get_plan_resource_list(self, plan, items_name):
        return self.get_resource_item_subitem(plan, items_name)

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################

    def create_plan(self, plan):
        return self.create_resource_item(plan)

    @deprecation.deprecate("use create_resource_item_subitem")
    def _create_plan_resource_item(self, plan, item_obj, items_name):
        return self.create_resource_item_subitem(plan, item_obj, items_name)

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    def get_plan(self, plan_id):
        return self.get_resource_item(plan_id)

    @deprecation.deprecate("use get_resource_item_subitem")
    def _get_plan_resource_item(self, plan, item_id, items_name, access_token=''):
        return self.get_resource_item_subitem(plan, item_id, depth_path=items_name, access_token=access_token)

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################

    def patch_plan(self, plan_id, patch_data, access_token=None):
        return self.patch_resource_item(plan_id, patch_data, access_token=access_token)

    @deprecation.deprecate("use patch_resource_item_subitem")
    def _patch_plan_resource_item(self, plan, item_obj, items_name):
        return self.patch_resource_item_subitem(plan, item_obj, depth_path=items_name)