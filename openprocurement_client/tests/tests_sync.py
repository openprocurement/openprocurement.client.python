from __future__ import print_function
from gevent import monkey; monkey.patch_all()

from openprocurement_client.client import TendersClientSync
from openprocurement_client.exceptions import (
    RequestFailed,
    PreconditionFailed,
    ResourceNotFound
)
from openprocurement_client.sync import (
    get_response,
    get_resource_items,
    get_tenders,
    ResourceFeeder,
)
from openprocurement_client.sync import logger

from gevent.queue import Queue
from munch import munchify
from StringIO import StringIO
from requests.exceptions import ConnectionError, InvalidHeader

import json
import logging
import mock
import unittest


class AlmostAlwaysTrue(object):
    def __init__(self, total_iterations=1):
        self.total_iterations = total_iterations
        self.current_iteration = 0

    def __nonzero__(self):
        if self.current_iteration < self.total_iterations:
            self.current_iteration += 1
            return bool(1)
        return bool(0)


class TestTendersClientSync(TendersClientSync):
    def __init__(self):
        pass


class GetResponseTestCase(unittest.TestCase):
    """"""

    def setUp(self):
        self.log_capture_string = StringIO()
        self.ch = logging.StreamHandler(self.log_capture_string)
        self.ch.setLevel(logging.ERROR)
        logger.addHandler(self.ch)
        self.logger = logger

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    def test_success_response(self, mock_sync_tenders):
        mock_sync_tenders.return_value = 'success'
        mock_client = TestTendersClientSync()
        response = get_response(mock_client, {})
        self.assertEqual(response, 'success')

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    def test_precondition_failed_error(self, mock_sync_tenders):
        mock_sync_tenders.side_effect = [PreconditionFailed(), 'success']
        mock_client = TestTendersClientSync()
        response = get_response(mock_client, {})
        log_strings = self.log_capture_string.getvalue().split('\n')
        self.assertEqual(log_strings[0], 'PreconditionFailed: Not described error yet.')
        self.assertEqual(response, 'success')

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    def test_connection_error(self, mock_sync_tenders):
        error = ConnectionError('connection error')
        mock_sync_tenders.side_effect = [error, error, 'success']
        mock_client = TestTendersClientSync()
        response = get_response(mock_client, {})
        log_strings = self.log_capture_string.getvalue().split('\n')
        self.assertEqual(log_strings[0], 'ConnectionError: connection error')
        self.assertEqual(log_strings[1], 'ConnectionError: connection error')
        self.assertEqual(response, 'success')

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    def test_request_failed_error(self, mock_sync_tenders):
        error1 = munchify({'status_code': 429, })
        error2 = munchify({'status_code': 404, })
        mock_sync_tenders.side_effect = [RequestFailed(error1), RequestFailed(error2), 'success']
        mock_client = TestTendersClientSync()
        response = get_response(mock_client, {})
        log_strings = self.log_capture_string.getvalue().split('\n')
        self.assertEqual(log_strings[0], 'Request failed. Status code: 429')
        self.assertEqual(log_strings[1], 'Request failed. Status code: 404')
        self.assertEqual(response, 'success')

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    def test_resource_not_found_error(self, mock_sync_tenders):
        mock_sync_tenders.side_effect = [ResourceNotFound(), 'success']
        params = {'offset': 'offset', 'some_data': 'data'}
        mock_client = TestTendersClientSync()
        mock_client.session = mock.MagicMock()
        mock_client.session.cookies.clear = mock.Mock()
        response = get_response(mock_client, params)
        log_strings = self.log_capture_string.getvalue().split('\n')
        self.assertEqual(log_strings[0], 'Resource not found: Not described error yet.')
        self.assertEqual(mock_client.session.cookies.clear.call_count, 1)
        self.assertEqual(params, {'some_data': 'data'})
        self.assertEqual(response, 'success')

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    def test_exception_error(self, mock_sync_tenders):
        mock_sync_tenders.side_effect = [InvalidHeader('invalid header'), Exception('exception message'), 'success']
        mock_client = TestTendersClientSync()
        response = get_response(mock_client, {})
        log_strings = self.log_capture_string.getvalue().split('\n')
        self.assertEqual(log_strings[0], 'Exception: invalid header')
        self.assertEqual(log_strings[1], 'Exception: exception message')
        self.assertEqual(response, 'success')


class ResourceFeederTestCase(unittest.TestCase):

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

    def test_instance_initialization(self):
        self.resource_feeder = ResourceFeeder()
        self.assertEqual(self.resource_feeder.key, '')
        self.assertEqual(self.resource_feeder.host, 'https://lb.api-sandbox.openprocurement.org/')
        self.assertEqual(self.resource_feeder.version, '2.3')
        self.assertEqual(self.resource_feeder.resource, 'tenders')
        self.assertEqual(self.resource_feeder.adaptive, False)
        self.assertEqual(self.resource_feeder.extra_params, {'opt_fields': 'status', 'mode': '_all_'})
        self.assertEqual(self.resource_feeder.retrievers_params, {
            'down_requests_sleep': 5,
            'up_requests_sleep': 1,
            'up_wait_sleep': 30,
            'up_wait_sleep_min': 5,
            'queue_size': 101
        })
        self.assertIsInstance(self.resource_feeder.queue, Queue)
        self.assertEqual(self.resource_feeder.forward_info, {})
        self.assertEqual(self.resource_feeder.backward_info, {})

    def test_init_api_clients(self):
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.init_api_clients()
        self.assertEqual(self.resource_feeder.backward_params, {
            'descending': True,
            'feed': 'changes',
            'opt_fields': 'status',
            'mode': '_all_'
        })
        self.assertEqual(self.resource_feeder.forward_params, {
            'feed': 'changes',
            'opt_fields': 'status',
            'mode': '_all_'
        })
        self.assertEqual(self.resource_feeder.forward_info, {'status': 1})
        self.assertEqual(self.resource_feeder.backward_info, {'status': 1})
        self.assertEqual(self.resource_feeder.forward_client.session.cookies,
                         self.resource_feeder.backward_client.session.cookies)

    def test_handle_response_data(self):
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.handle_response_data(['tender1', 'tender2'])
        self.assertIn('tender1', list(self.resource_feeder.queue.queue))
        self.assertIn('tender2', list(self.resource_feeder.queue.queue))
        self.assertNotIn('tender3', list(self.resource_feeder.queue.queue))

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    @mock.patch('openprocurement_client.sync.spawn')
    def test_start_sync(self, mock_spawn, mock_sync_tenders):
        mock_spawn.return_value = 'spawn result'
        mock_sync_tenders.return_value = self.response
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.init_api_clients()
        self.resource_feeder.start_sync()
        self.assertEqual(self.resource_feeder.backward_params['offset'], self.response.next_page.offset)
        self.assertEqual(self.resource_feeder.forward_params['offset'], self.response.prev_page.offset)
        self.assertEqual(self.resource_feeder.forward_params['offset'], self.response.prev_page.offset)
        self.assertEqual(mock_spawn.call_count, 2)
        mock_spawn.assert_called_with(self.resource_feeder.retriever_forward)
        self.assertEqual(self.resource_feeder.backward_worker, 'spawn result')
        self.assertEqual(self.resource_feeder.forward_worker, 'spawn result')

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    @mock.patch('openprocurement_client.sync.spawn')
    def test_restart_sync(self, mock_spawn, mock_sync_tenders):
        mock_spawn.return_value = mock.MagicMock()
        mock_spawn.return_value.kill = mock.MagicMock('kill result')
        mock_sync_tenders.return_value = self.response
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.init_api_clients()
        self.resource_feeder.start_sync()
        self.resource_feeder.restart_sync()
        self.assertEqual(mock_spawn.return_value.kill.call_count, 2)

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    @mock.patch('openprocurement_client.sync.spawn')
    def test_get_resource_items_zero_value(self, mock_spawn, mock_sync_tenders):
        mock_sync_tenders.side_effect = [self.response, munchify(
            {'data': {}, 'next_page': {'offset': 'next_page'}, 'prev_page': {'offset': 'next_page'}}
        )]
        mock_spawn.return_value = mock.MagicMock()
        mock_spawn.return_value.value = 0
        self.resource_feeder = ResourceFeeder()
        mock_spawn.return_value.ready.return_value = True
        with mock.patch('__builtin__.True', AlmostAlwaysTrue(4)):
            result = self.resource_feeder.get_resource_items()
        self.assertEqual(tuple(result), tuple(self.response.data))

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    @mock.patch('openprocurement_client.sync.spawn')
    def test_get_resource_items_non_zero_value(self, mock_spawn, mock_sync_tenders):
        mock_sync_tenders.side_effect = [self.response, munchify(
            {'data': {}, 'next_page': {'offset': 'next_page'}, 'prev_page': {'offset': 'next_page'}}
        )]
        mock_spawn.return_value = mock.MagicMock()
        mock_spawn.return_value.value = 1
        self.resource_feeder = ResourceFeeder()
        mock_spawn.return_value.ready.side_effect = [True, False]
        with mock.patch('__builtin__.True', AlmostAlwaysTrue(4)):
            result = self.resource_feeder.get_resource_items()
        self.assertEqual(tuple(result), tuple(self.response.data))

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    @mock.patch('openprocurement_client.sync.spawn')
    @mock.patch('openprocurement_client.sync.sleep')
    def test_feeder_zero_value(self, mock_sleep, mock_spawn, mock_sync_tenders):
        mock_sleep.return_value = 'sleeping'
        mock_sync_tenders.side_effect = [self.response, self.response, ConnectionError('conn error')]
        self.resource_feeder = ResourceFeeder()
        mock_spawn.return_value = mock.MagicMock()
        mock_spawn.return_value.value = 0
        mock_spawn.return_value.ready.return_value = True
        with self.assertRaises(ConnectionError) as e:
            self.resource_feeder.feeder()
        self.assertEqual(e.exception.message, 'conn error')
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch('openprocurement_client.client.TendersClientSync.sync_tenders')
    @mock.patch('openprocurement_client.sync.spawn')
    @mock.patch('openprocurement_client.sync.sleep')
    def test_feeder(self, mock_sleep, mock_spawn, mock_sync_tenders):
        mock_sleep.return_value = 'sleeping'
        mock_sync_tenders.side_effect = [self.response, self.response, ConnectionError('conn error')]
        self.resource_feeder = ResourceFeeder()
        mock_spawn.return_value = mock.MagicMock()
        mock_spawn.return_value.value = 1
        mock_spawn.return_value.ready.side_effect = [True, False, False, True]
        with self.assertRaises(ConnectionError) as e:
            self.resource_feeder.feeder()
        self.assertEqual(e.exception.message, 'conn error')
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch('openprocurement_client.sync.spawn')
    def test_run_feeder(self, mock_spawn):
        mock_spawn.return_value = mock.MagicMock()
        self.resource_feeder = ResourceFeeder()
        result = self.resource_feeder.run_feeder()
        mock_spawn.assert_called_with(self.resource_feeder.feeder)
        self.assertEqual(result, self.resource_feeder.queue)

    @mock.patch('openprocurement_client.sync.get_response')
    def test_retriever_backward(self, mock_get_response):
        mock_get_response.side_effect = [self.response, munchify({'data': {}})]
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.init_api_clients()
        self.resource_feeder.backward_params = {"limit": 0}
        self.resource_feeder.backward_client = mock.MagicMock()
        self.resource_feeder.cookies = self.resource_feeder.backward_client.session.cookies
        self.resource_feeder.retriever_backward()
        self.assertEqual(self.resource_feeder.backward_params['offset'], self.response.next_page.offset)
        self.assertEqual(self.resource_feeder.backward_info['resource_item_count'], 0)
        self.assertEqual(self.resource_feeder.backward_info['status'], 0)

    @mock.patch('openprocurement_client.sync.get_response')
    def test_retriever_backward_wrong_cookies(self, mock_get_response):
        mock_get_response.return_value = self.response
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.init_api_clients()
        self.resource_feeder.backward_params = {"limit": 0}
        self.resource_feeder.backward_client = mock.MagicMock()
        self.resource_feeder.cookies = mock.MagicMock()
        self.resource_feeder.backward_client.session.cookies = mock.MagicMock()
        with self.assertRaises(Exception) as e:
            self.resource_feeder.retriever_backward()
        self.assertEqual(e.exception.message, 'LB Server mismatch')

    @mock.patch('openprocurement_client.sync.get_response')
    def test_retriever_forward_wrong_cookies(self, mock_get_response):
        mock_get_response.return_value = self.response
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.init_api_clients()
        self.resource_feeder.backward_params = {"limit": 0}
        self.resource_feeder.backward_client = mock.MagicMock()
        self.resource_feeder.cookies = mock.MagicMock()
        self.resource_feeder.backward_client.session.cookies = mock.MagicMock()
        with self.assertRaises(Exception) as e:
            self.resource_feeder.retriever_forward()
        self.assertEqual(e.exception.message, 'LB Server mismatch')

    @mock.patch('openprocurement_client.sync.get_response')
    def test_retriever_forward(self, mock_get_response):
        mock_get_response.side_effect = [
            self.response,
            self.response,
            ConnectionError('connection error')
        ]
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.init_api_clients()
        self.resource_feeder.forward_params = {"limit": 0}
        self.resource_feeder.forward_client = mock.MagicMock()
        self.resource_feeder.forward_client.session.cookies = self.resource_feeder.cookies
        with self.assertRaises(ConnectionError) as e:
            self.resource_feeder.retriever_forward()
        self.assertEqual(e.exception.message, 'connection error')
        self.assertEqual(self.resource_feeder.forward_params['offset'], self.response.next_page.offset)
        self.assertEqual(self.resource_feeder.forward_info['resource_item_count'], 3)
        self.assertEqual(self.resource_feeder.forward_info['status'], 3)

    @mock.patch('openprocurement_client.sync.get_response')
    def test_retriever_forward_no_data(self, mock_get_response):
        mock_get_response.side_effect = [
            munchify({'data': {}, 'next_page': {'offset': 'next_page'}}),
            ConnectionError('connection error')
        ]
        self.resource_feeder = ResourceFeeder()
        self.resource_feeder.init_api_clients()
        self.resource_feeder.forward_params = {"limit": 0}
        self.resource_feeder.forward_client = mock.MagicMock()
        self.resource_feeder.forward_client.session.cookies = self.resource_feeder.cookies
        with self.assertRaises(ConnectionError) as e:
            self.resource_feeder.retriever_forward()
        self.assertEqual(e.exception.message, 'connection error')
        self.assertEqual(self.resource_feeder.forward_params['offset'], 'next_page')
        self.assertEqual(self.resource_feeder.forward_info['resource_item_count'], 0)
        self.assertEqual(self.resource_feeder.forward_info['status'], 3)

    @mock.patch('openprocurement_client.sync.get_response')
    def test_retriever_forward_adaptive(self, mock_get_response):
        mock_get_response.side_effect = [
            self.response,
            munchify({'data': {}, 'next_page': {'offset': 'next_page'}}),
            self.response,
            ConnectionError('connection error')
        ]
        self.resource_feeder = ResourceFeeder(adaptive=True)
        self.resource_feeder.init_api_clients()
        self.resource_feeder.forward_params = {"limit": 0}
        self.resource_feeder.forward_client = mock.MagicMock()
        self.resource_feeder.forward_client.session.cookies = self.resource_feeder.cookies
        with self.assertRaises(ConnectionError) as e:
            self.resource_feeder.retriever_forward()
        self.assertEqual(e.exception.message, 'connection error')
        self.assertEqual(self.resource_feeder.forward_params['offset'], self.response.next_page.offset)
        self.assertEqual(self.resource_feeder.forward_info['resource_item_count'], 3)
        self.assertEqual(self.resource_feeder.forward_info['status'], 3)

    @mock.patch('openprocurement_client.sync.get_response')
    def test_retriever_forward_no_data_adaptive(self, mock_get_response):
        mock_get_response.side_effect = [
            munchify({'data': {}, 'next_page': {'offset': 'next_page'}}),
            munchify({'data': {}, 'next_page': {'offset': 'next_page'}}),
            ConnectionError('connection error')
        ]
        self.resource_feeder = ResourceFeeder(
            adaptive=True,
            retrievers_params={
                'down_requests_sleep': 5,
                'up_requests_sleep': 1,
                'up_wait_sleep': 15,
                'up_wait_sleep_min': 5,
                'queue_size': 101
            }
        )
        self.resource_feeder.init_api_clients()
        self.resource_feeder.forward_params = {"limit": 0}
        self.resource_feeder.forward_client = mock.MagicMock()
        self.resource_feeder.forward_client.session.cookies = self.resource_feeder.cookies
        with self.assertRaises(ConnectionError) as e:
            self.resource_feeder.retriever_forward()
        self.assertEqual(e.exception.message, 'connection error')
        self.assertEqual(self.resource_feeder.forward_params['offset'], 'next_page')
        self.assertEqual(self.resource_feeder.forward_info['resource_item_count'], 0)
        self.assertEqual(self.resource_feeder.forward_info['status'], 3)

    @mock.patch('openprocurement_client.sync.ResourceFeeder.get_resource_items')
    def test_get_resource_items(self, mock_get_resource_items):
        mock_get_resource_items.return_value = 'feeder_instance'
        result = get_resource_items(resource='tenders')
        self.assertEqual(result, 'feeder_instance')
        self.assertEqual(mock_get_resource_items.call_count, 1)

    @mock.patch('openprocurement_client.sync.get_resource_items')
    def test_get_tenders(self, mock_get_resource_items):
        mock_get_resource_items.return_value = 'get_resource_items_call'
        result = get_tenders()
        self.assertEqual(result, 'get_resource_items_call')
        self.assertEqual(mock_get_resource_items.call_count, 1)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GetResponseTestCase))
    suite.addTest(unittest.makeSuite(ResourceFeederTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
