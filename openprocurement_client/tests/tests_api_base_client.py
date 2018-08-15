import unittest
import uuid
from mock import MagicMock
from json import dumps
from copy import deepcopy

from openprocurement_client.api_base_client import APIBaseClient
from openprocurement_client.exceptions import InvalidResponse


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
        class Response(object):
            def __init__(self, status_code, text=None, headers=None):
                self.status_code = status_code
                self.text = text
                self.headers = headers

        revisions_limit = 42
        response_text = {
            "id": uuid.uuid4().hex,
            "rev": 24
        }

        side_effect = [
            Response(200, dumps(response_text), {"x-revision-n": str(revisions_limit)}),
            Response(200, dumps(response_text), {"x-revision-n": str(revisions_limit)}),
            Response(200, dumps(response_text), {"x-revision-n": str(revisions_limit - 1)}),
            Response(404),
            Response(404),
            Response(404),
        ]

        self.client.request = MagicMock(side_effect=side_effect)

        actual_response = deepcopy(response_text)
        actual_response["x_revision_n"] = str(revisions_limit)
        item_id = response_text["id"]
        self.assertEqual(self.client.get_resource_item_historical(item_id, revision=""), actual_response)
        self.assertEqual(self.client.get_resource_item_historical(item_id, revision=revisions_limit), actual_response)
        actual_response["x_revision_n"] = str(revisions_limit - 1)
        self.assertEqual(self.client.get_resource_item_historical(
            item_id, revision=revisions_limit - 1), actual_response)

        for revision in (0, revisions_limit + 1, None):
            with self.assertRaises(InvalidResponse) as e:
                self.client.get_resource_item_historical(item_id, revision=revision)
            self.assertEqual(e.exception.status_code, 404)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAPIBaseClient))
    return suite


if __name__ == "__main__":
    unittest.main(defaultTest='suite')