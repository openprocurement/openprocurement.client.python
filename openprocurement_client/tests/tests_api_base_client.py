import unittest
import uuid
from mock import MagicMock
from copy import deepcopy
from datetime import datetime
from openprocurement_client.api_base_client import APIBaseClient


CLIENT_CONFIG = {
    "key": "",
    "resource": "tenders",
    "host_url": "http://lb.api-sandbox.openprocurement.org/",
    "api_version": "2.4"
}


class TestAPIBaseClient(unittest.TestCase):
    def setUp(self):
        self.client = APIBaseClient(**CLIENT_CONFIG)

    def test_get_resource_item_historical(self):
        item = {
            "id": uuid.uuid4().hex,
            "dateModified": datetime.now()
        }
        response = {
            "data": deepcopy(item),
            "x_revision_n": "5"
        }

        def side_effect(_, headers):
            return item if headers["x-revision-n"] else response

        self.client._get_resource_item = MagicMock(side_effect=side_effect)

        self.assertEqual(self.client.get_resource_item_historical("", revision=""), response)
        self.assertEqual(self.client.get_resource_item_historical("", revision="54"), item)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAPIBaseClient))
    return suite


if __name__ == "__main__":
    unittest.main(defaultTest='suite')