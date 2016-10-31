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
        self.prefix_path = '/api/{}'.format(api_version)
        
    def change_owner_item(self, url, payload):
        response_item = self.post(url, payload=dumps(payload))   
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    ### Tender and his subpage owner change
    #
    
    def create_transfer(self):
        return self._create_resource_item('{}/transfers'.format(self.prefix_path), {"data":{}})

    def get_transfer(self, id):
        return self._get_resource_item('{}/transfers/{}'.format(self.prefix_path, id))
    
    def change_bid_owner(self, tender_id, bid_id, bid_transfer):
        tr_data = self.create_transfer()
        data = { "data": { "transfer": bid_transfer, "id": tr_data.data.id}}
        url = '{}/tenders/{}/{}/{}/{}'.format(self.prefix_path, tender_id, "bids", bid_id, "ownership")
        return self.change_owner_item( url, payload=dumps(data))
    
    def change_tender_owner(self, tender_id, tender_transfer):
        tr_data = self.create_transfer()
        data = { "data": { "transfer": tender_transfer, "id": tr_data.data.id}}
        url = '{}/tenders/{}/ownership'.format(self.prefix_path, tender_id)
        return self.change_owner_item( url, payload=dumps(data))
    
    def change_complaint_owner(self, tender_id, complaint_id, complaint_transfer):
        tr_data = self.create_transfer()
        data = { "data": { "transfer": complaint_transfer, "id": tr_data.data.id}}
        url = '{}/tenders/{}/{}/{}/{}'.format(self.prefix_path, tender_id, "complaints", complaint_id, "ownership")
        return self.change_owner_item( url, payload=dumps(data))
    
    ### Others owner change
    #
    
    def patch_contract(self, contract_id, tender):
        url = '{}/contracts/{}/credentials'.format(self.prefix_path, contract_id)
        return self._patch_resource_item( url, payload={'data': ''}, headers={'X-Access-Token': getattr(getattr(tender, 'access', ''), 'token', '')})
    
    
    def change_contract_owner(self, contract_id, tender):
        tr_data = self.create_transfer()
        contract = self.patch_contract(contract_id, tender)
        url = '{}/contracts/{}/ownership'.format(self.prefix_path, contract.data.id)
        data = {"data": {"id": tr_data.data.id, 'transfer': contract.access.transfer}}
        return self.change_owner_item(url, payload=dumps(data)) 
