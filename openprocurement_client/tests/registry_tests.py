from __future__ import print_function
from gevent import monkey;

monkey.patch_all()
from gevent.pywsgi import WSGIServer
from bottle import Bottle
from StringIO import StringIO
from collections import Iterable
from simplejson import loads, load
from munch import munchify
import mock
import sys
import unittest
from openprocurement_client.registry_client import RegistryClient, RegistryClientSync

from openprocurement_client.document_service_client \
    import DocumentServiceClient
from openprocurement_client.exceptions import InvalidResponse, ResourceNotFound

from openprocurement_client.tests.data_dict import TEST_ASSET_KEYS, TEST_LOT_KEYS, \
    TEST_TENDER_KEYS_LIMITED, TEST_PLAN_KEYS, TEST_CONTRACT_KEYS
from openprocurement_client.tests._server import \
    API_KEY, API_VERSION, AUTH_DS_FAKE, DS_HOST_URL, DS_PORT, \
    HOST_URL, location_error, PORT, ROOT, setup_routing, setup_routing_ds, \
    resource_partition, resource_filter


class BaseTestClass(unittest.TestCase):
    def setting_up(self, client, resource=None):
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
        ds_client = getattr(self, 'ds_client', None)
        self.client = client('', host_url=HOST_URL, api_version=API_VERSION,
                             ds_client=ds_client)
        if resource:
            self.client = client('', host_url=HOST_URL, api_version=API_VERSION,
                                 ds_client=ds_client, resource=resource)

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

        cls.ds_client = DocumentServiceClient(host_url=DS_HOST_URL,
                                              auth_ds=AUTH_DS_FAKE)
        # to test units performing file operations outside the DS uncomment
        # following lines:
        # import logging
        # logging.basicConfig()
        # cls.ds_client = None

        setup_routing_ds(cls.app_ds)

    @classmethod
    def setUpClass(cls):
        cls.setting_up_ds()

    @classmethod
    def tearDownClass(cls):
        cls.server_ds.stop()


class AssetsRegistryTestCase(BaseTestClass):
    def setUp(self):
        self.setting_up(client=RegistryClient, resource='assets')

        with open(ROOT + 'assets.json') as assets:
            self.assets = munchify(load(assets))
        with open(ROOT + 'asset_{}.json'.format(TEST_ASSET_KEYS.asset_id)) as asset:
            self.asset = munchify(load(asset))

    def tearDown(self):
        self.server.stop()

    def test_get_assets(self):
        setup_routing(self.app, routes=["assets"])
        assets = self.client.get_assets()
        self.assertIsInstance(assets, Iterable)
        self.assertEqual(assets['data'], self.assets.data)

    @mock.patch('openprocurement_client.registry_client.RegistryClient.request')
    def test_get_assets_failed(self, mock_request):
        mock_request.return_value = munchify({'status_code': 404})
        self.client.params['offset'] = 'offset_value'
        with self.assertRaises(InvalidResponse) as e:
            self.client.get_assets()

    def test_get_asset(self):
        setup_routing(self.app, routes=["asset"])
        asset = self.client.get_asset(TEST_ASSET_KEYS.asset_id)
        self.assertEqual(asset, self.asset)

    def test_patch_asset(self):
        setup_routing(self.app, routes=["asset_patch"])
        self.asset.data.description = 'test_patch_asset'

        patched_asset = self.client.patch_asset(self.asset)
        self.assertEqual(patched_asset.data.id, self.asset.data.id)
        self.assertEqual(patched_asset.data.description, self.asset.data.description)


class LotsRegistryTestCase(BaseTestClass):
    def setUp(self):
        self.setting_up(client=RegistryClient, resource='lots')

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
        self.assertEqual(lots['data'], self.lots.data)

    @mock.patch('openprocurement_client.registry_client.RegistryClient.request')
    def test_get_lots_failed(self, mock_request):
        mock_request.return_value = munchify({'status_code': 404})
        self.client.params['offset'] = 'offset_value'
        with self.assertRaises(InvalidResponse) as e:
            self.client.get_lots()

    def test_get_lot(self):
        setup_routing(self.app, routes=["lot"])
        lot = self.client.get_lot(TEST_LOT_KEYS.lot_id)
        self.assertEqual(lot, self.lot)

    def test_patch_lot(self):
        setup_routing(self.app, routes=["lot_patch"])
        self.lot.data.description = 'test_patch_lot'

        patched_lot = self.client.patch_lot(self.lot)
        self.assertEqual(patched_lot.data.id, self.lot.data.id)
        self.assertEqual(patched_lot.data.description, self.lot.data.description)


class AssetsClientSyncTestCase(BaseTestClass):
    """"""

    def setUp(self):
        self.setting_up(client=RegistryClientSync, resource='assets')

        with open(ROOT + 'assets.json') as assets:
            self.assets = munchify(load(assets))
        with open(ROOT + 'asset_' + TEST_ASSET_KEYS.asset_id + '.json') as asset:
            self.asset = munchify(load(asset))

    def tearDown(self):
        self.server.stop()

    def test_sync_assets(self):
        setup_routing(self.app, routes=['assets'])
        assets = self.client.sync_item()
        self.assertIsInstance(assets.data, Iterable)
        self.assertEqual(assets.data, self.assets.data)


class LotsClientSyncTestCase(BaseTestClass):
    """"""

    def setUp(self):
        self.setting_up(client=RegistryClientSync)

        with open(ROOT + 'lots.json') as lots:
            self.lots = munchify(load(lots))
        with open(ROOT + 'lot_' + TEST_ASSET_KEYS.lot_id + '.json') as lot:
            self.lot = munchify(load(lot))

    def tearDown(self):
        self.server.stop()

    def test_sync_lots(self):
        setup_routing(self.app, routes=['lots'])
        lots = self.client.sync_item()
        self.assertIsInstance(lots.data, Iterable)
        self.assertEqual(lots.data, self.lots.data)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AssetsRegistryTestCase))
    suite.addTest(unittest.makeSuite(LotsRegistryTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
