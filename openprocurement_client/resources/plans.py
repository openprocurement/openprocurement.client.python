from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import PLANS
import logging


LOGGER = logging.getLogger(__name__)


class PlansClient(APIResourceClient):
    """Client for plans"""

    api_version = '0'
    resource = PLANS

    ###########################################################################
    #             GET ITEMS LIST API METHODS
    ###########################################################################

    def get_plans(self, params=None, feed='changes'):
        return self.get_resource_items(params, feed)

    def get_latest_plans(self, date):
        return self.get_latest_resource_items(date)

    def _get_plan_resource_list(self, plan, items_name):
        return self._get_resource_item(
            '{}/{}/{}'.format(self.prefix_path, plan.data.id, items_name),
            headers={'X-Access-Token': self._get_access_token(plan)}
        )

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################

    def create_plan(self, plan):
        return self.create_resource_item(plan)

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    def get_plan(self, plan_id):
        return self.get_resource_item(plan_id)

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################

    def patch_plan(self, plan_id, patch_data, access_token=None):
        return self.patch_resource_item(
            plan_id, patch_data, access_token=access_token
        )
