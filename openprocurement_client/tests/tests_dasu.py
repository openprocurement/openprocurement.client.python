from __future__ import print_function
from simplejson import load
from munch import munchify
import mock
import unittest
from openprocurement_client.dasu_client import DasuClient
from openprocurement_client.tests.data_dict import TEST_MONITORING_KEYS
from openprocurement_client.tests._server import  ROOT


class TestDasuClient(DasuClient):
    def __init__(self, params=None):
        if params is None:
            self.params = {}


class TestUtilsFunctions(unittest.TestCase):

    def setUp(self):

        with open(ROOT + 'monitoring_' + TEST_MONITORING_KEYS.monitoring_id + '.json') as monitoring:
            self.monitoring = munchify(load(monitoring))

    @mock.patch('openprocurement_client.api_base_client.APIBaseClient._create_resource_item')
    @mock.patch('openprocurement_client.dasu_client.DasuClient.create_monitoring')
    def test_create_monitoring(self, mock_create_resource_item, mock_create_monitoring):
        mock_create_resource_item.return_value = self.monitoring
        client = TestDasuClient()
        result = client.create_monitoring(self.monitoring)
        self.assertEqual(result, self.monitoring)

    @mock.patch('openprocurement_client.api_base_client.APIBaseClient._get_resource_item')
    @mock.patch('openprocurement_client.dasu_client.DasuClient.get_monitoring')
    def test_get_monitoring(self, mock_get_resource_item, mock_get_monitoring):
        mock_get_resource_item.return_value = self.monitoring
        client = TestDasuClient()
        result = client.get_monitoring(self.monitoring.data.id)
        self.assertEqual(result, self.monitoring)

    @mock.patch('openprocurement_client.dasu_client.DasuClient.get_monitorings')
    def test_get_monitorings(self, mock_get_monitorings):
        monitorings = [self.monitoring]
        mock_get_monitorings.side_effect = [monitorings]
        client = TestDasuClient()
        result = client.get_monitorings()
        self.assertEqual(result, monitorings)

    @mock.patch('openprocurement_client.dasu_client.DasuClient.patch_monitoring')
    def test_patch_monitoring(self, mock_patch_monitoring):
        patched_data = self.monitoring
        patched_data.data.status = "addressed"
        mock_patch_monitoring.side_effect = [patched_data]
        client = TestDasuClient()
        result = client.patch_monitoring(patched_data, self.monitoring.data.id)
        self.assertEqual(result, patched_data)

    @mock.patch('openprocurement_client.dasu_client.DasuClient.patch_appeal')
    def test_patch_appeal(self, mock_patch_appeal):
        appeal_data = {"data": {"description": TEST_MONITORING_KEYS.description}}
        patched_data = self.monitoring
        patched_data["data"]["appeal"] = appeal_data["data"]
        mock_patch_appeal.side_effect = [patched_data]
        client = TestDasuClient()
        result = client.patch_appeal(self.monitoring, appeal_data)
        self.assertEqual(result, patched_data)

    @mock.patch('openprocurement_client.dasu_client.DasuClient.patch_eliminationReport')
    def test_patch_eliminationReport(self, mock_patch_eliminationReport):
        report_data = {"data": {"description": TEST_MONITORING_KEYS.description}}
        patched_data = self.monitoring
        patched_data["data"]["eliminationReport"] = report_data["data"]
        mock_patch_eliminationReport.side_effect = [patched_data]
        client = TestDasuClient()
        result = client.patch_eliminationReport(self.monitoring, report_data)
        self.assertEqual(result, patched_data)

    @mock.patch('openprocurement_client.dasu_client.DasuClient.patch_post')
    def test_patch_post(self, mock_patch_post):
        post_data = {"data": {"description": TEST_MONITORING_KEYS.description,
                              "title": TEST_MONITORING_KEYS.title } }
        patched_data = self.monitoring
        patched_data["data"]["post"] =  [post_data["data"]]
        mock_patch_post.side_effect = [patched_data]
        client = TestDasuClient()
        result = client.patch_post(self.monitoring, post_data, TEST_MONITORING_KEYS.dialogue_id)
        self.assertEqual(result, patched_data)

    @mock.patch('openprocurement_client.dasu_client.DasuClient.create_post')
    def test_create_post(self, mock_create_post):
        post_data = {"data": {"description": TEST_MONITORING_KEYS.description,
                              "title": TEST_MONITORING_KEYS.title } }
        patched_data = self.monitoring
        patched_data["data"]["post"] =  [post_data["data"]]
        mock_create_post.side_effect = [patched_data]
        client = TestDasuClient()
        result = client.create_post(self.monitoring, post_data)
        self.assertEqual(result, patched_data)

    @mock.patch('openprocurement_client.dasu_client.DasuClient.create_party')
    def test_create_party(self, mock_create_party):
        party_data = {"data": { "name": TEST_MONITORING_KEYS.name,
                                "roles": [TEST_MONITORING_KEYS.roles] }}
        patched_data = self.monitoring
        patched_data["data"]["parties"].append(party_data["data"])
        mock_create_party.side_effect = [patched_data]
        client = TestDasuClient()
        result = client.create_party(self.monitoring, party_data)
        self.assertEqual(result, patched_data)

    @mock.patch('openprocurement_client.dasu_client.DasuClient.upload_obj_document')
    def test_upload_obj_document(self, mock_get_monitoring):
        file_name = "test_document.txt"
        file_path = ROOT + file_name
        doc_data = {"data": { "title": file_name, "id": TEST_MONITORING_KEYS.document_id } }
        mock_get_monitoring.side_effect = [doc_data]
        client = TestDasuClient()
        result = client.upload_obj_document( file_path, self.monitoring)
        self.assertEqual(result, doc_data)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtilsFunctions))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
