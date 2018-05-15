from json import loads
from munch import munchify

from .clients import APIBaseClient, verify_file


class ContractingClient(APIBaseClient):
    """ contracting client """

    def __init__(self, key,
                 host_url="https://api-sandbox.openprocurement.org",
                 api_version='2.0',
                 params=None):
        super(ContractingClient, self).__init__(
            key,
            "contracts",
            host_url,
            api_version,
            params,
        )

    @verify_file
    def upload_document(self, file_, contract):
        return self._upload_resource_file(
            '{}/{}/documents'.format(
                self.prefix_path,
                contract.data.id
            ),
            file_=file_,
            headers={'X-Access-Token':
                     getattr(getattr(contract, 'access', ''), 'token', '')}
        )

    def create_contract(self, contract):
        return self._create_resource_item(self.prefix_path, contract)

    def get_contract(self, contract_id):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, contract_id))

    def get_contracts(self, params=None, feed='changes'):
        if params is None:
            params = {}
        params['feed'] = feed
        self._update_params(params)
        response = self.get(
            self.prefix_path,
            params_dict=self.params)
        if response.status_int == 200:
            data = munchify(loads(response.body_string()))
            self._update_params(data.next_page)
            return data.data
