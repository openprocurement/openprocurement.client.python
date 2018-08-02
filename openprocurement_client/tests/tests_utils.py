from __future__ import print_function
from gevent import monkey; monkey.patch_all()

from openprocurement_client.client import TendersClient
from openprocurement_client.exceptions import IdNotFound
from openprocurement_client.utils import tenders_feed,  \
    get_tender_id_by_uaid, get_tender_by_uaid, get_monitoring_id_by_uaid
from tests_dasu import TestDasuClient

from munch import munchify

import json
import mock
import unittest


class TestTendersClient(TendersClient):
    def __init__(self, params=None):
        if params is None:
            self.params = {}


class TestUtilsFunctions(unittest.TestCase):

    def setUp(self):
        self.response = munchify(json.loads("""
                {
                   "next_page":{
                      "path":"/api/0.10/tenders?offset=2015-12-25T18%3A04%3A36.264176%2B02%3A00",
                      "uri":"https://lb.api-sandbox.openprocurement.org/api/0.10/tenders?offset=2015-12-25T18%3A04%3A36.264176%2B02%3A00",
                      "offset":"2015-12-25T18:04:36.264176+02:00"
                   },
                   "prev_page":{
                      "path":"/api/0.10/tenders?offset=2015-12-25T18%3A04%3A36.264176%2B02%3A00",
                      "uri":"https://lb.api-sandbox.openprocurement.org/api/0.10/tenders?offset=2015-12-25T18%3A04%3A36.264176%2B02%3A00",
                      "offset":"2015-12-25T18:04:36.264176+02:00"
                   },
                   "data":[
                      {
                         "id":"823d50b3236247adad28a5a66f74db42",
                         "dateModified":"2015-11-13T18:50:00.753811+02:00"
                      },
                      {
                         "id":"f3849ade33534174b8402579152a5f41",
                         "dateModified":"2015-11-16T01:15:00.469896+02:00"
                      },
                      {
                         "id":"f3849ade33534174b8402579152a5f41",
                         "dateModified":"2015-11-16T12:00:00.960077+02:00"
                      }
                   ]
                }"""))

    @mock.patch('openprocurement_client.client.TendersClient.get_tenders')
    def test_tenders_feed(self, mock_get_tenders):
        mock_get_tenders.side_effect = [self.response.data, []]
        client = TestTendersClient()
        result = tenders_feed(client, 1)
        self.assertEqual(result.next(), self.response.data[0])
        self.assertEqual(result.next(), self.response.data[1])
        self.assertEqual(result.next(), self.response.data[2])
        with self.assertRaises(StopIteration):
            result.next()

    @mock.patch('openprocurement_client.utils.get_tender_id_by_uaid')
    @mock.patch('openprocurement_client.client.TendersClient.get_tender')
    def test_get_tender_by_uaid(self, mock_get_tender, mock_get_tender_id_by_uaid):
        mock_get_tender_id_by_uaid.return_value = 'tender_id'
        mock_get_tender.return_value = 'called get_tender'
        client = TestTendersClient()
        result = get_tender_by_uaid('ua_id', client)
        mock_get_tender_id_by_uaid.assert_called_with('ua_id', client)
        mock_get_tender.assert_called_with('tender_id')
        self.assertEqual(mock_get_tender_id_by_uaid.call_count, 1)
        self.assertEqual(mock_get_tender.call_count, 1)
        self.assertEqual(result, 'called get_tender')

    @mock.patch('openprocurement_client.client.TendersClient.get_tenders')
    def test_get_tender_id_by_uaid(self, mock_get_tenders):
        mock_get_tenders.side_effect = [self.response.data, []]
        client = TestTendersClient()
        with self.assertRaises(IdNotFound):
            result = get_tender_id_by_uaid('f3849ade33534174b8402579152a5f41', client, id_field='dateModified')
            self.assertEqual(result, self.response.data[0]['id'])

    @mock.patch('openprocurement_client.dasu_client.DasuClient.get_monitorings')
    @mock.patch('openprocurement_client.utils.get_monitoring_id_by_uaid')
    def test_get_monitoring_id_by_uaid(self, mock_get_monitorings, mock_get_monitoring_id_by_uaid):
        monitoring_id = 'f32f928d57d8485890b694cb2e02f864'
        monitoring_uaid = 'UA-M-2018-07-31-000074'
        monitorings = munchify({"monitoring_id": monitoring_uaid, "id": monitoring_id})
        mock_get_monitoring_id_by_uaid.side_effect = [[monitorings]]
        client = TestDasuClient()
        result = get_monitoring_id_by_uaid(monitoring_uaid, client)
        self.assertEqual(result, monitoring_id)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtilsFunctions))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
