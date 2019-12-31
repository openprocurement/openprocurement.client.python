import hashlib
from openprocurement_client.templates import APITemplateClient
from openprocurement_client.exceptions import InvalidResponse
from openprocurement_client.constants import CRITERIA

from openprocurement_client.compatibility_utils import munchify_factory

from simplejson import loads


munchify = munchify_factory()
IGNORE_PARAMS = ('uri', 'path')


class CriteriaServiceClient(APITemplateClient):
    """class for work with Document Service"""

    host_url = 'https://api-sandbox.openprocurement.org'
    api_version = '0'
    headers = {'Content-Type': 'application/json'}
    resource = CRITERIA

    def __init__(self,
                 host_url='',
                 api_version=None,
                 auth_criteria=None,
                 headers=None):

        super(CriteriaServiceClient, self)\
            .__init__(login_pass=auth_criteria, headers=headers)

        self.api_version = api_version or self.api_version
        self.host_url = host_url or self.host_url
        self.prefix_path = '{}/api/{}/{}/'.format(self.host_url, self.api_version, self.resource)

    def create_criteria(self, criteria):
        response_item = self.request(
            'POST', path=self.prefix_path,
            json=criteria, headers=None
        )
        return munchify(loads(response_item.content))

    def get_criteria(self, criteria_id):
        path = '{}{}'.format(self.prefix_path, criteria_id)
        response_item = self.request(
            'GET', path=path
        )
        return munchify(loads(response_item.content))

    def patch_criteria(self, criteria_id, data):
        path = '{}{}/'.format(self.prefix_path, criteria_id)
        response_item = self.request('PATCH', path, json=data)
        return munchify(loads(response_item.content))

    def delete_criteria(self, criteria_id):
        path = '{}{}/'.format(self.prefix_path, criteria_id)
        response_item = self.request('DELETE', path)
        return munchify(loads(response_item.content))