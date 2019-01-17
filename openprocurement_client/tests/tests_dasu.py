from simplejson import load
from munch import munchify
import mock
import unittest
from openprocurement_client.dasu_client import DasuClient
from openprocurement_client.tests.data_dict import TEST_MONITORING_KEYS
from openprocurement_client.tests.tests_resources import BaseTestClass
from json import dumps


from openprocurement_client.tests._server import (
    AUTH_DS_FAKE,
    DS_HOST_URL,
    ROOT,
)


class Response(object):
    def __init__(self, status_code, text=None, headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers


class TestUtilsFunctions(unittest.TestCase):

    def setUp(self):
        with open(ROOT + 'monitoring_' + TEST_MONITORING_KEYS.monitoring_id + '.json') as monitoring:
            self.monitoring = munchify(load(monitoring))
        with open(ROOT + 'monitorings.json') as monitorings:
            self.monitorings = munchify(load(monitorings))
    
    ds_config = {
        'host_url': DS_HOST_URL,
        'auth_ds': AUTH_DS_FAKE
        }

    client = DasuClient('', ds_config=ds_config)


    def test_create_monitoring(self):
        side_effect = [
            Response(201, dumps(self.monitoring))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.create_monitoring(self.monitoring)
        self.assertEqual(result, self.monitoring)

    def test_get_monitoring(self):
        side_effect = [
            Response(200, dumps(self.monitoring))
            ]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.get_monitoring(self.monitoring.data.id)
        self.assertEqual(result, self.monitoring)

    def test_get_monitorings(self):
        side_effect = [Response(200, dumps(self.monitorings))]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.get_monitorings()
        self.assertEqual(result, self.monitorings.data)

    def test_patch_monitoring(self):
        patched_data = self.monitoring
        patched_data.data.status = "addressed"
        side_effect = [
            Response(200, dumps(patched_data))
            ]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.patch_monitoring(patched_data, self.monitoring.data.id)
        self.assertEqual(result, patched_data)

    def test_patch_appeal(self):
        appeal_data = {"data": {"description": TEST_MONITORING_KEYS.description}}
        patched_data = self.monitoring
        patched_data["data"]["appeal"] = appeal_data["data"]
        side_effect = [
            Response(200, dumps(patched_data)),
            ]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.patch_appeal(self.monitoring, appeal_data)
        self.assertEqual(result, patched_data)

    def test_patch_eliminationReport(self):
        report_data = {"data": {"description": TEST_MONITORING_KEYS.description}}
        patched_data = self.monitoring
        patched_data["data"]["eliminationReport"] = report_data["data"]
        side_effect = [
            Response(200, dumps(patched_data)),
            ]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.patch_eliminationReport(self.monitoring, report_data)
        self.assertEqual(result, patched_data)

    def test_patch_post(self):
        post_data = {"data": {"description": TEST_MONITORING_KEYS.description,
                              "title": TEST_MONITORING_KEYS.title } }
        patched_data = self.monitoring
        patched_data["data"]["post"] = [post_data["data"]]
        side_effect = [
            Response(200, dumps(patched_data)),
            ]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.patch_post(self.monitoring,
                                        post_data,
                                        TEST_MONITORING_KEYS.dialogue_id)
        self.assertEqual(result, patched_data)

    def test_create_post(self):
        post_data = {"data": {"description": TEST_MONITORING_KEYS.description,
                              "title": TEST_MONITORING_KEYS.title } }
        patched_data = self.monitoring
        patched_data["data"]["post"] =  [post_data["data"]]
        side_effect = [
            Response(201, dumps(patched_data)),
            ]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.create_post(self.monitoring, post_data)
        self.assertEqual(result, patched_data)

    def test_create_party(self):
        party_data = {"data": { "name": TEST_MONITORING_KEYS.name,
                                "roles": [TEST_MONITORING_KEYS.roles] }}
        patched_data = self.monitoring
        patched_data["data"]["parties"].append(party_data["data"])
        side_effect = [
            Response(201, dumps(patched_data)),
            ]
        self.client.request = mock.MagicMock(side_effect=side_effect)
        result = self.client.create_party(self.monitoring, party_data)
        self.assertEqual(result, patched_data)

    def test_upload_obj_document(self):
        BaseTestClass.setUpClass()
        file_name = "test_document.txt"
        file_path = ROOT + file_name
        result = self.client.upload_obj_document(file_path, self.monitoring)
        BaseTestClass.tearDownClass()
        self.assertEqual(result.data.title, file_name)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtilsFunctions))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')