from client import APIBaseClient, InvalidResponse
from iso8601 import parse_date
from munch import munchify
from restkit import BasicAuth, errors, request, Resource
from retrying import retry
from simplejson import dumps, loads
import logging

logger = logging.getLogger(__name__)

class PlansClient(APIBaseClient):
    """client for plans"""

    def __init__(self, key,
                 host_url="https://api-sandbox.openprocurement.org",
                 api_version='0.8',
                 params=None):
        super(PlansClient, self).__init__(key, host_url,api_version, "plans", params)

    ###########################################################################
    #             GET ITEMS LIST API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_plans(self, params={}, feed='changes'):
        params['feed'] = feed
        try:
            self._update_params(params)
            response = self.get(
                self.prefix_path,
                params_dict=self.params)
            if response.status_int == 200:
                plan_list = munchify(loads(response.body_string()))
                self._update_params(plan_list.next_page)
                return plan_list.data

        except errors.ResourceNotFound:
            del self.params['offset']
            raise

        raise InvalidResponse

    def get_latest_plans(self, date, plan_id):
        iso_dt = parse_date(date)
        dt = iso_dt.strftime("%Y-%m-%d")
        tm = iso_dt.strftime("%H:%M:%S")
        response = self._get_resource_item(
            '{}?offset={}T{}&opt_fields=plan_id&mode=test'.format(
                self.prefix_path,
                dt,
                tm
            )
        )
        if response.status_int == 200:
            plan_list = munchify(loads(response.body_string()))
            self._update_params(plan_list.next_page)
            return plan_list.data
        raise InvalidResponse

    def _get_plan_resource_list(self, plan, items_name):
        return self._get_resource_item(
            '{}/{}/{}'.format(self.prefix_path, plan.data.id, items_name),
            headers={'X-Access-Token':
                     getattr(getattr(plan, 'access', ''), 'token', '')}
        )

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################

    def _create_plan_resource_item(self, plan, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, plan.data.id, items_name),
            item_obj,
            headers={'X-Access-Token':
                     getattr(getattr(plan, 'access', ''), 'token', '')}
        )

    def create_plan(self, plan):
        return self._create_resource_item(self.prefix_path, plan)

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    def get_plan(self, id):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id))

    def _get_plan_resource_item(self, plan, item_id, items_name,
                                  access_token=""):
        if access_token:
            headers = {'X-Access-Token': access_token}
        else:
            headers = {'X-Access-Token':
                       getattr(getattr(tender, 'access', ''), 'token', '')}
        return self._get_resource_item(
            '{}/{}/{}/{}'.format(self.prefix_path,
                                 tender.data.id,
                                 items_name,
                                 item_id),
            headers=headers
        )

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################

    def _patch_plan_resource_item(self, plan, item_obj, items_name):
        return self._patch_resource_item(
            '{}/{}/{}/{}'.format(
                self.prefix_path, plan.data.id, items_name, item_obj['data']['id']
            ),
            payload=item_obj,
            headers={'X-Access-Token':
                     getattr(getattr(plan, 'access', ''), 'token', '')}
        )

    def patch_plan(self, plan):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, plan["data"]["id"]),
            payload=plan,
            headers={'X-Access-Token':
                     getattr(getattr(plan, 'access', ''), 'token', '')}
        )
