# -*- coding: utf-8 -*-
from openprocurement_client.compatibility_utils import munchify_factory

from simplejson import loads

from openprocurement_client.exceptions import InvalidResponse
from openprocurement_client.templates import APITemplateClient


munchify = munchify_factory()


class EDRClient(APITemplateClient):
    """ Client for validate members by EDR """

    host_url = 'https://lb-api-staging.prozorro.gov.ua'
    api_version = '2.5'

    def __init__(self, host_url=None, api_version=None, username=None,
                 password=None):
        super(EDRClient, self).__init__(login_pass=(username, password))
        self.host_url = host_url or self.host_url
        self.api_version = api_version or self.api_version

    def verify_member(self, edrpou, extra_headers=None):
        self.headers.update(extra_headers or {})
        response = self.request(
            'GET', '{}/api/{}/verify'.format(self.host_url, self.api_version), params_dict={'id': edrpou}
        )
        if response.status_code == 200:
            return munchify(loads(response.text))
        raise InvalidResponse(response)
