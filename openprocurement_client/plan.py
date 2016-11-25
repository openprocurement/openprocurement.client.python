from client import APIBaseClient, InvalidResponse
from iso8601 import parse_date
from munch import munchify
from retrying import retry
from simplejson import dumps, loads
import logging

logger = logging.getLogger(__name__)


class PlansClient(APIBaseClient):
    """client for plans"""

    api_version = '0.8'

    def __init__(self,
                 key,
                 host_url=None,
                 api_version=None,
                 params=None):

        _api_version = api_version or self.api_version
        super(PlansClient, self)\
            .__init__(key, 'plans', host_url, _api_version, params)

    ###########################################################################
    #             GET ITEMS LIST API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_plans(self, params={}, feed='changes'):
        params['feed'] = feed
        self._update_params(params)
        response = self.request('GET',
            self.prefix_path,
            params_dict=self.params)
        if response.status_code == 200:
            plan_list = munchify(loads(response.text))
            self._update_params(plan_list.next_page)
            return plan_list.data
        elif response.status_code == 412:
            del self.params['offset']

        raise InvalidResponse

    def get_latest_plans(self, date):
        iso_dt = parse_date(date)
        dt = iso_dt.strftime('%Y-%m-%d')
        tm = iso_dt.strftime('%H:%M:%S')
        response = self._get_resource_item(
            '{}?offset={}T{}&opt_fields=plan_id&mode=test'.format(
                self.prefix_path,
                dt,
                tm
            )
        )
        if response.status_code == 200:
            plan_list = munchify(loads(response.text))
            self._update_params(plan_list.next_page)
            return plan_list.data
        raise InvalidResponse

    def _get_plan_resource_list(self, plan, items_name):
        return self._get_resource_item(
            '{}/{}/{}'.format(self.prefix_path, plan.data.id, items_name),
            headers={'X-Access-Token': self._get_access_token(plan)}
        )

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################

    def _create_plan_resource_item(self, plan, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, plan.data.id, items_name),
            item_obj,
            headers={'X-Access-Token': self._get_access_token(plan)}
        )

    def create_plan(self, plan):
        return self._create_resource_item(self.prefix_path, plan)

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    def get_plan(self, plan_id):
        return self._get_resource_item('{}/{}'
                                       .format(self.prefix_path, plan_id))

    def _get_plan_resource_item(self, plan, item_id, items_name,
                                access_token=''):
        if access_token:
            headers = {'X-Access-Token': access_token}
        else:
            headers = {'X-Access-Token': self._get_access_token(plan)}
        return self._get_resource_item(
            '{}/{}/{}/{}'.format(self.prefix_path,
                                 plan.data.id,
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
                self.prefix_path, plan.data.id,
                items_name, item_obj['data']['id']
            ),
            payload=item_obj,
            headers={'X-Access-Token': self._get_access_token(plan)}
        )

    def patch_plan(self, plan):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, plan['data']['id']),
            payload=plan,
            headers={'X-Access-Token': self._get_access_token(plan)}
        )
