from __future__ import print_function
from gevent import monkey
monkey.patch_all()

import mock
import sys
import unittest
import uuid
from copy import deepcopy
from json import dumps
from gevent.pywsgi import WSGIServer
from bottle import Bottle
from collections import Iterable
from simplejson import load
from munch import munchify
from openprocurement_client.resources.assets import AssetsClient
from openprocurement_client.resources.lots import LotsClient
from openprocurement_client.clients import APIBaseClient
from openprocurement_client.exceptions import InvalidResponse
from openprocurement_client.tests.data_dict import (
    TEST_ASSET_KEYS,
    TEST_LOT_KEYS,
)
from openprocurement_client.tests._server import \
    API_VERSION, AUTH_DS_FAKE, DS_HOST_URL, DS_PORT, \
    HOST_URL, PORT, ROOT, setup_routing, setup_routing_ds, \
    resource_filter


class BaseTestClass(unittest.TestCase):
    def setting_up(self, client):
        self.app = Bottle()
        self.app.router.add_filter('resource_filter', resource_filter)
        setup_routing(self.app)
        self.server = WSGIServer(('localhost', PORT), self.app, log=None)
        try:
            self.server.start()
        except Exception as error:
            print(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2],
                  file=sys.stderr)
            raise error

        ds_config = {
            'host_url': DS_HOST_URL,
            'auth_ds': AUTH_DS_FAKE
        }
        self.client = client('', host_url=HOST_URL, api_version=API_VERSION,
                             ds_config=ds_config)

    @classmethod
    def setting_up_ds(cls):
        cls.app_ds = Bottle()
        cls.server_ds \
            = WSGIServer(('localhost', DS_PORT), cls.app_ds, log=None)
        try:
            cls.server_ds.start()
        except Exception as error:
            print(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2],
                  file=sys.stderr)
            raise error

        setup_routing_ds(cls.app_ds)

    @classmethod
    def setUpClass(cls):
        cls.setting_up_ds()

    @classmethod
    def tearDownClass(cls):
        cls.server_ds.stop()


class AssetsRegistryTestCase(BaseTestClass):
    def setUp(self):
        self.setting_up(client=AssetsClient)

        with open(ROOT + 'assets.json') as assets:
            self.assets = munchify(load(assets))
        with open(ROOT + 'asset_{}.json'.format(
                TEST_ASSET_KEYS.asset_id)) as asset:
            self.asset = munchify(load(asset))

    def tearDown(self):
        self.server.stop()

    def test_get_assets(self):
        setup_routing(self.app, routes=["assets"])
        assets = self.client.get_assets()
        self.assertIsInstance(assets, Iterable)
        self.assertEqual(assets, self.assets.data)

    @mock.patch('openprocurement_client.resources.assets.AssetsClient.request')
    def test_get_assets_failed(self, mock_request):
        mock_request.return_value = munchify({'status_code': 404})
        with self.assertRaises(InvalidResponse):
            self.client.get_assets(params={'offset': 'offset_value'})

    def test_get_asset(self):
        setup_routing(self.app, routes=["asset"])
        asset = self.client.get_asset(TEST_ASSET_KEYS.asset_id)
        self.assertEqual(asset, self.asset)

    def test_patch_asset(self):
        setup_routing(self.app, routes=["asset_patch"])
        asset_id = self.asset.data.id
        patch_data = {'data': {'description': 'test_patch_asset'}}
        patched_asset = self.client.patch_resource_item(asset_id,
                                                        patch_data)
        self.assertEqual(patched_asset.data.id, self.asset.data.id)
        self.assertEqual(patched_asset.data.description,
                         patch_data['data']['description'])


class LotsRegistryTestCase(BaseTestClass):
    def setUp(self):
        self.setting_up(client=LotsClient)

        with open(ROOT + 'lots.json') as lots:
            self.lots = munchify(load(lots))
        with open(ROOT + 'lot_{}.json'.format(TEST_LOT_KEYS.lot_id)) as lot:
            self.lot = munchify(load(lot))

    def tearDown(self):
        self.server.stop()

    def test_get_lots(self):
        setup_routing(self.app, routes=["lots"])
        lots = self.client.get_lots()
        self.assertIsInstance(lots, Iterable)
        self.assertEqual(lots, self.lots.data)

    @mock.patch('openprocurement_client.resources.lots.LotsClient.request')
    def test_get_lots_failed(self, mock_request):
        mock_request.return_value = munchify({'status_code': 404})
        with self.assertRaises(InvalidResponse):
            self.client.get_lots(params={'offset': 'offset_value'})

    def test_get_lot(self):
        setup_routing(self.app, routes=["lot"])
        lot = self.client.get_lot(TEST_LOT_KEYS.lot_id)
        self.assertEqual(lot, self.lot)

    def test_patch_lot(self):
        setup_routing(self.app, routes=["lot_patch"])
        lot_id = self.lot.data.id
        patch_data = {'data': {'description': 'test_patch_lot'}}
        patched_lot = self.client.patch_resource_item(lot_id, patch_data)
        self.assertEqual(patched_lot.data.id, lot_id)
        self.assertEqual(patched_lot.data.description,
                         patch_data['data']['description'])


class APIBaseClientTestCase(BaseTestClass):
    def setUp(self):
        self.setting_up(client=APIBaseClient)

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

        self.client.request = mock.MagicMock(side_effect=side_effect)

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

    def tearDown(self):
        self.server.stop()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AssetsRegistryTestCase))
    suite.addTest(unittest.makeSuite(LotsRegistryTestCase))
    suite.addTest(unittest.makeSuite(APIBaseClientTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
