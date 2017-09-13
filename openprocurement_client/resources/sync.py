from gevent import monkey
monkey.patch_all()

import logging
from openprocurement_client.clients import APIResourceClientSync
from openprocurement_client.utils import get_response

from gevent import spawn, sleep, idle
from gevent.queue import Queue, Empty


DEFAULT_RETRIEVERS_PARAMS = {
    'down_requests_sleep': 5,
    'up_requests_sleep': 1,
    'up_wait_sleep': 30,
    'up_wait_sleep_min': 5,
    'queue_size': 101
}

DEFAULT_API_HOST = 'https://lb.api-sandbox.openprocurement.org/'
DEFAULT_API_VERSION = '2.3'
DEFAULT_API_KEY = ''
DEFAULT_API_EXTRA_PARAMS = {
    'opt_fields': 'status', 'mode': '_all_'}

LOGGER = logging.getLogger(__name__)


class ResourceFeeder(object):
    idle = idle

    def __init__(self, host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
                 key=DEFAULT_API_KEY, resource='tenders',
                 extra_params=DEFAULT_API_EXTRA_PARAMS,
                 retrievers_params=DEFAULT_RETRIEVERS_PARAMS, adaptive=False):
        super(ResourceFeeder, self).__init__()
        self.host = host
        self.version = version
        self.key = key
        self.resource = resource
        self.adaptive = adaptive

        self.extra_params = extra_params
        self.retrievers_params = retrievers_params
        self.queue = Queue(maxsize=retrievers_params['queue_size'])

    def init_api_clients(self):
        self.backward_params = {'descending': True, 'feed': 'changes'}
        self.backward_params.update(self.extra_params)
        self.forward_params = {'feed': 'changes'}
        self.forward_params.update(self.extra_params)
        self.forward_client = APIResourceClientSync(
            self.key, resource=self.resource, host_url=self.host,
            api_version=self.version)
        self.backward_client = APIResourceClientSync(
            self.key, resource=self.resource, host_url=self.host,
            api_version=self.version)
        self.cookies = self.forward_client.session.cookies =\
            self.backward_client.session.cookies

    def handle_response_data(self, data):
        for resource_item in data:
            # self.idle()
            self.queue.put(resource_item)

    def start_sync(self):
        # self.init_api_clients()

        response = self.backward_client.sync_resource_items(
            self.backward_params)

        self.handle_response_data(response.data)

        self.backward_params['offset'] = response.next_page.offset
        self.forward_params['offset'] = response.prev_page.offset

        self.backward_worker = spawn(self.retriever_backward)
        self.forward_worker = spawn(self.retriever_forward)

    def restart_sync(self):
        """
        Restart retrieving from Openprocurement API.
        """

        LOGGER.info('Restart workers')
        self.forward_worker.kill()
        self.backward_worker.kill()
        self.init_api_clients()
        self.start_sync()

    def get_resource_items(self):
        """
        Prepare iterator for retrieving from Openprocurement API.

        :param:
            host (str): Url of Openprocurement API.
                Defaults is DEFAULT_API_HOST
            version (str): Verion of Openprocurement API.
                Defaults is DEFAULT_API_VERSION
            key(str): Access key of broker in Openprocurement API.
                Defaults is DEFAULT_API_KEY
                (Empty string)
            extra_params(dict): Extra params of query

        :returns:
            iterator of tender_object (Munch): object derived from the
                list of tenders

        """
        self.init_api_clients()
        self.start_sync()
        check_down_worker = True
        while True:
            if check_down_worker and self.backward_worker.ready():
                if self.backward_worker.value == 0:
                    LOGGER.info('Stop check backward worker')
                    check_down_worker = False
                else:
                    self.restart_sync()
                    check_down_worker = True
            if self.forward_worker.ready():
                self.restart_sync()
                check_down_worker = True
            while not self.queue.empty():
                yield self.queue.get()
            try:
                self.queue.peek(block=True, timeout=0.1)
            except Empty:
                pass

    def feeder(self):
        """
        Prepare iterator for retrieving from Openprocurement API.

        :param:
            host (str): Url of Openprocurement API.
                Defaults is DEFAULT_API_HOST
            version (str): Verion of Openprocurement API.
                Defaults is DEFAULT_API_VERSION
            key(str): Access key of broker in Openprocurement API.
                Defaults is DEFAULT_API_KEY
                (Empty string)
            extra_params(dict): Extra params of query

        :returns:
            iterator of tender_object (Munch): object derived from the
                list of tenders

        """
        self.init_api_clients()
        self.start_sync()
        check_down_worker = True
        while 1:
            if check_down_worker and self.backward_worker.ready():
                if self.backward_worker.value == 0:
                    LOGGER.info('Stop check backward worker')
                    check_down_worker = False
                else:
                    self.restart_sync()
                    check_down_worker = True
            if self.forward_worker.ready():
                self.restart_sync()
                check_down_worker = True
            LOGGER.debug('Feeder queue size {} items'.format(
                self.queue.qsize()),
                extra={'FEEDER_QUEUE_SIZE': self.queue.qsize()})
            sleep(2)

    def run_feeder(self):
        spawn(self.feeder)
        return self.queue

    def retriever_backward(self):
        LOGGER.info('Backward: Start worker')
        response = get_response(self.backward_client, self.backward_params)
        LOGGER.debug('Backward response length {} items'.format(
            len(response.data)),
            extra={'BACKWARD_RESPONSE_LENGTH': len(response.data)})
        if self.cookies != self.backward_client.session.cookies:
            raise Exception('LB Server mismatch')
        while response.data:
            LOGGER.debug('Backward: Start process data.')
            self.handle_response_data(response.data)
            self.backward_params['offset'] = response.next_page.offset
            self.log_retriever_state(
                'Backward', self.backward_client, self.backward_params)
            LOGGER.debug('Backward: Start process request.')
            response = get_response(self.backward_client, self.backward_params)
            LOGGER.debug('Backward response length {} items'.format(
                len(response.data)),
                extra={'BACKWARD_RESPONSE_LENGTH': len(response.data)})
            if self.cookies != self.backward_client.session.cookies:
                raise Exception('LB Server mismatch')
            LOGGER.info('Backward: pause between requests {} sec.'.format(
                self.retrievers_params.get('down_requests_sleep', 5)))
            sleep(self.retrievers_params.get('down_requests_sleep', 5))
        LOGGER.info('Backward: finished')
        return 0

    def retriever_forward(self):
        LOGGER.info('Forward: Start worker')
        response = get_response(self.forward_client, self.forward_params)
        LOGGER.debug('Forward response length {} items'.format(
            len(response.data)),
            extra={'FORWARD_RESPONSE_LENGTH': len(response.data)})
        if self.cookies != self.forward_client.session.cookies:
            raise Exception('LB Server mismatch')
        while 1:
            while response.data:
                self.handle_response_data(response.data)
                self.forward_params['offset'] = response.next_page.offset
                self.log_retriever_state(
                    'Forward', self.forward_client, self.forward_params)
                response = get_response(self.forward_client,
                                        self.forward_params)
                LOGGER.debug('Forward response length {} items'.format(
                    len(response.data)),
                    extra={'FORWARD_RESPONSE_LENGTH': len(response.data)})
                if self.cookies != self.forward_client.session.cookies:
                    raise Exception('LB Server mismatch')
                if len(response.data) != 0:
                    LOGGER.info(
                        'Forward: pause between requests {} sec.'.format(
                            self.retrievers_params.get('up_requests_sleep',
                                                       5.0)))
                    sleep(self.retrievers_params.get('up_requests_sleep', 5.0))
            LOGGER.info('Forward: pause after empty response {} sec.'.format(
                self.retrievers_params.get('up_wait_sleep', 30.0)),
                extra={'FORWARD_WAIT_SLEEP':
                       self.retrievers_params.get('up_wait_sleep', 30.0)})
            sleep(self.retrievers_params.get('up_wait_sleep', 30.0))
            self.forward_params['offset'] = response.next_page.offset
            self.log_retriever_state(
                'Forward', self.forward_client, self.forward_params)
            response = get_response(self.forward_client, self.forward_params)
            LOGGER.debug('Forward response length {} items'.format(
                len(response.data)),
                extra={'FORWARD_RESPONSE_LENGTH': len(response.data)})
            if self.adaptive:
                if len(response.data) != 0:
                    if (self.retrievers_params['up_wait_sleep'] >
                            self.retrievers_params['up_wait_sleep_min']):
                        self.retrievers_params['up_wait_sleep'] -= 1
                else:
                    if self.retrievers_params['up_wait_sleep'] < 30:
                        self.retrievers_params['up_wait_sleep'] += 1
            if self.cookies != self.forward_client.session.cookies:
                raise Exception('LB Server mismatch')

        return 1

    def log_retriever_state(self, name, client, params):
        LOGGER.debug('{}: offset {}'.format(name, params.get('offset', '')))
        LOGGER.debug('{}: AWSELB {}'.format(
            name,
            client.session.cookies.get('AWSELB', ' ')
        ))
        LOGGER.debug('{}: SERVER_ID {}'.format(
            name, client.session.cookies.get('SERVER_ID', '')
        ))
        LOGGER.debug('{}: limit {}'.format(name, params.get('limit', '')))
