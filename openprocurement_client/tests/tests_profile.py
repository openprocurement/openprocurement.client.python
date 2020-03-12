from simplejson import load
from openprocurement_client.compatibility_utils import munchify_factory

import mock
import unittest
from openprocurement_client.resources.profile import ProfileServiceClient
from json import dumps


from openprocurement_client.tests._server import (
    ROOT,
    API_VERSION,
    AUTH_DS_FAKE,
    BASIS_URL
)


munchify = munchify_factory()


class Response(object):
    def __init__(self, status_code, content=None, headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers


class TestProfileFunctions(unittest.TestCase):

    client = ProfileServiceClient(host_url=BASIS_URL,
                                  api_version=API_VERSION,
                                  auth_profile=AUTH_DS_FAKE)

    def setUp(self):
        with open(ROOT + 'profile.json') as profile_data:
            self.profile_data = munchify(load(profile_data))

    def test_create_profile(self):
        # Arrange
        side_effect = [
            Response(201, dumps(self.profile_data))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        data = self.profile_data['data']
        # Act
        result = self.client.create_profile(data)
        # Assert
        self.assertEqual(result, self.profile_data)

    def test_get_profile(self):
        # Arrange
        side_effect = [
            Response(200, dumps(self.profile_data['data']))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        profile_id = self.profile_data['data']['id']
        data = self.profile_data['data']
        # Act
        result = self.client.get_profile(profile_id)
        # Assert
        self.assertEqual(result, data)

    def test_patch_profile(self):
        # Arrange
        data_for_change = {'access': self.profile_data['access'], 'data': {'title': 'TestTitle'}}
        side_effect = [
            Response(200, dumps(self.profile_data['data']))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        profile_id = self.profile_data['data']['id']
        data = self.profile_data['data']
        # Act
        result = self.client.patch_profile(profile_id, data_for_change)
        # Assert
        self.assertEqual(result, data)

    def test_delete_profile(self):
        # Arrange
        access = {'access': self.profile_data['access']}
        side_effect = [
            Response(200, dumps(self.profile_data['data']))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        profile_id = self.profile_data['data']['id']
        data = self.profile_data['data']
        # Act
        result = self.client.delete_profile(profile_id, access)
        # Assert
        self.assertEqual(result, data)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestProfileFunctions))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
