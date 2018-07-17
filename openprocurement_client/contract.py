from simplejson import loads
from munch import munchify
from client import APIBaseClient
from openprocurement_client.exceptions import ResourceNotFound, InvalidResponse


class ContractingClient(APIBaseClient):
    """ contracting client """

    def __init__(self,
                 key,
                 host_url=None,
                 api_version=None,
                 params=None,
                 ds_client=None):
        super(ContractingClient, self).__init__(key, 'contracts', host_url,
                                                api_version, params, ds_client)

    def create_contract(self, contract):
        return self._create_resource_item(self.prefix_path, contract)

    def get_contract(self, id):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id))

    def get_contracts(self, params=None, feed='changes'):
        _params = (params or {}).copy()
        _params['feed'] = feed
        self._update_params(_params)
        try:
            response = self.request('GET', self.prefix_path,
                                    params_dict=self.params)
        except ResourceNotFound as e:
            self.params.pop('offset', None)
            raise e
        if response.status_code == 200:
            contracts = munchify(loads(response.text))
            self._update_params(contracts.next_page)
            return contracts.data

        raise InvalidResponse(response)

    def _create_contract_resource_item(self, contract_id, access_token, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, contract_id, items_name),
            item_obj,
            headers={'X-Access-Token': access_token}
        )

    def create_change(self, contract_id, access_token, change_data):
        return self._create_contract_resource_item(contract_id, access_token, change_data,
                                                    "changes")

    def retrieve_contract_credentials(self, contract_id, access_token):
        # In order to get rights for future contract editing, tender token is passed as access token here.
        # Response will contain the new access token for further contract modification.
        return self._patch_resource_item(
            '{}/{}/credentials'.format(self.prefix_path, contract_id),
            payload=None,
            headers={'X-Access-Token': access_token}
        )

    def patch_contract(self, contract_id, access_token, data):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, contract_id),
            payload=data,
            headers={'X-Access-Token': access_token}
        )

    def patch_change(self, contract_id, change_id, access_token, data):
        return self._patch_resource_item(
            '{}/{}/{}/{}'.format(self.prefix_path, contract_id, 'changes',
                                 change_id),
            payload=data,
            headers={'X-Access-Token': access_token}
        )

    def patch_milestone(self, contract_id, access_token, data):
        return self._patch_resource_item(
            '{}/{}/{}/{}'.format(self.prefix_path, contract_id, 'milestones',
                                data['data']['id']),
            payload=data,
            headers={'X-Access-Token': access_token}
        )