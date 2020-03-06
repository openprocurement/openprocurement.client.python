#!/usr/bin/python
# -*- coding: utf-8 -*-
from openprocurement_client.templates import APITemplateClient
from openprocurement_client.constants import PROFILE
from openprocurement_client.compatibility_utils import munchify_factory
from simplejson import loads

munchify = munchify_factory()


class ProfileServiceClient(APITemplateClient):

    headers = {'Content-Type': 'application/json'}
    resource = PROFILE

    def __init__(
            self,
            host_url='',
            api_version=None,
            auth_profile=None,
            headers=None,
            ):
        super(ProfileServiceClient,
              self).__init__(login_pass=auth_profile, headers=headers)

        self.api_version = api_version or self.api_version
        self.host_url = host_url or self.host_url
        self.prefix_path = '{}/api/{}/{}/'.format(
                                self.host_url, self.api_version, self.resource)

    def create_profile(self, data_profile):
        response = self.request('POST', path=self.prefix_path,
                                json=data_profile)
        return munchify(loads(response.content))

    def get_profile(self, id_profile):
        path = '{}{}/'.format(self.prefix_path, id_profile)
        response = self.request('GET', path=path)
        return munchify(loads(response.content))

    def patch_profile(self, id_profile, data_profile):
        path = '{}{}/'.format(self.prefix_path, id_profile)
        response = self.request('PATCH', path=path, json=data_profile)
        return munchify(loads(response.content))

    def delete_profile(self, id_profile, data_profile):
        path = '{}{}/'.format(self.prefix_path, id_profile)
        response = self.request('DELETE', path=path, json=data_profile)
        return munchify(loads(response.content))
