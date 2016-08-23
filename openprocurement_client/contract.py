from json import loads
from munch import munchify
from client import APIBaseClient, verify_file
from restkit.errors import ResourceNotFound


class ContractingClient(APIBaseClient):
    """ contracting client """

    def __init__(self, key,
                 host_url="https://api-sandbox.openprocurement.org",
                 api_version='2.0',
                 params=None):
        super(ContractingClient, self).__init__(key, host_url, api_version,
                                                "contracts", params)

    @verify_file
    def upload_document(self, file_, contract_id, access_token):
        return self._upload_resource_file(
            '{}/{}/documents'.format(
                self.prefix_path,
                contract_id
            ),
            data={"file": file_},
            headers={'X-Access-Token': access_token}
        )

    def create_contract(self, contract):
        return self._create_resource_item(self.prefix_path, contract)

    def get_contract(self, id):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id))

    def get_contracts(self, params={}, feed='changes'):
        params['feed'] = feed
        try:
            self._update_params(params)
            response = self.get(
                self.prefix_path,
                params_dict=self.params)
            if response.status_int == 200:
                contract_list = munchify(loads(response.body_string()))
                self._update_params(contract_list.next_page)
                return contract_list.data

        except ResourceNotFound:
            self.params.pop('offset', 'None')
            raise

        raise InvalidResponse

    def _create_contract_resource_item(self, contract_id, access_token, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, contract_id, items_name),
            item_obj,
            headers={'X-Access-Token': access_token}
        )

    def create_change(self, contract_id, access_token, change_data):
        return self._create_contract_resource_item(contract_id, access_token, change_data, "changes")

    def get_contract_credentials(self, contract_id, access_token):
        return self._patch_resource_item(
            '{}/{}/credentials'.format(self.prefix_path, contract_id),
            payload={},
            headers={'X-Access-Token': access_token}
        )

    def patch_document(self, contract_id, document_id, access_token, data):
        return self._patch_resource_item(
            "{}/{}/{}/{}".format(self.prefix_path, contract_id, "documents", document_id
            ),
            payload=data,
            headers={'X-Access-Token': access_token}
        )

    def patch_contract(self, contract_id, access_token, data):
        return self._patch_resource_item(
            "{}/{}".format(self.prefix_path, contract_id),
            payload=data,
            headers={'X-Access-Token': access_token}
        )

    def patch_change(self, contract_id, change_id, access_token, data):
        return self._patch_resource_item(
            "{}/{}/{}/{}".format(self.prefix_path, contract_id, "changes", change_id),
            payload=data,
            headers={'X-Access-Token': access_token}
        )
