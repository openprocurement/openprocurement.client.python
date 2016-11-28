from json import loads
from munch import munchify
from client import APIBaseClient, verify_file


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

    @verify_file
    def upload_document(self, file_, contract):
        return self._upload_resource_file(
            '{}/{}/documents'.format(
                self.prefix_path,
                contract.data.id
            ),
            files=file_,
            headers={'X-Access-Token': self._get_access_token(contract)}
        )

    def create_contract(self, contract):
        return self._create_resource_item(self.prefix_path, contract)

    def get_contract(self, id):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id))

    def get_contracts(self, params={}, feed='changes'):
        params['feed'] = feed
        self._update_params(params)
        response = self.request('GET',
                                self.prefix_path,
                                params_dict=self.params)
        if response.status_code == 200:
            data = munchify(loads(response.text))
            self._update_params(data.next_page)
            return data.data
