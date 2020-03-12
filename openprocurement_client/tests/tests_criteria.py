from simplejson import load
from openprocurement_client.compatibility_utils import munchify_factory

import mock
import unittest
from openprocurement_client.resources.criteria import CriteriaServiceClient
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


class TestCriteriaFunctions(unittest.TestCase):

    client = CriteriaServiceClient(host_url=BASIS_URL,
                                   api_version=API_VERSION,
                                   auth_criteria=AUTH_DS_FAKE)

    def setUp(self):
        with open(ROOT + 'criteria.json') as criteria_data:
            self.criteria_data = munchify(load(criteria_data))

    def test_create_criteria(self):
        # Arrange
        side_effect = [
            Response(201, dumps(self.criteria_data))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        # Act
        result = self.client.create_criteria(self.criteria_data)
        # Assert
        self.assertEqual(result, self.criteria_data)

    def test_get_criteria(self):
        # Arrange
        side_effect = [
            Response(200, dumps(self.criteria_data))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        criteria_id = self.criteria_data['id']
        # Act
        result = self.client.get_criteria(criteria_id)
        # Assert
        self.assertEqual(result, self.criteria_data)

    def test_patch_criteria(self):
        # Arrange
        data = {'title': 'TestTitle'}
        side_effect = [
            Response(200, dumps(self.criteria_data))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        criteria_id = self.criteria_data['id']
        # Act
        result = self.client.patch_criteria(criteria_id, data)
        # Assert
        self.assertEqual(result, self.criteria_data)

    def test_delete_profile(self):
        # Arrange
        side_effect = [
            Response(200, dumps(self.criteria_data))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        criteria_id = self.criteria_data['id']
        # Act
        result = self.client.delete_criteria(criteria_id)
        # Assert
        self.assertEqual(result, self.criteria_data)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCriteriaFunctions))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
