from client import TendersClient
from json import loads, dumps
from munch import munchify

class Ownerchange(TendersClient):
    def __init__(self, key,
                 host_url="https://api-sandbox.openprocurement.org",
                 api_version='2.0',
                 params=None,
                 resource=''):
        super(Ownerchange, self).__init__(key, host_url, api_version, resource, params)
        self.transfer_path = '/api/{}/transfers'.format(api_version)
        self.prefix_path = '/api/{}/tenders'.format(api_version)

    def _change_ownership(self, transfer, item_id, item_path):
        tr_data = self.create_transfer()
        data = { "data": { "transfer": transfer, "id": tr_data.access.transfer}}
        url = '{}/{}/ownership'.format(item_path, item_id)
        response_item = self.post(url, payload=dumps(data))   
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def create_transfer(self):
        return self._create_resource_item(self.transfer_path, {"data":{}})

    def get_transfer(self, id):
        return self._get_resource_item('{}/{}'.format(self.transfer_path, id))

    def change_bid_owner(self, tender_id, bid_id, transfer):
        path = '{}/{}/{}'.format(self.prefix_path, tender_id, "bids")
        return self._change_ownership(transfer, bid_id, path)
    
    def change_tender_owner(self, tender_id, transfer):
        return self._change_ownership(transfer, tender_id, self.prefix_path)
    
    def change_complaint_owner(self, tender_id, complaint_id, transfer):
        path = '{}/{}/{}'.format(self.prefix_path, tender_id, "complaints")
        return self._change_ownership(transfer, complaint_id, path)

    def change_contract_owner(self, tender_id, contract_id, transfer):
        path = '{}/{}/{}'.format(self.prefix_path, tender_id, "contracts")
        return self._change_ownership(transfer, contract_id, path)
