from gevent import monkey
monkey.patch_all()

import logging
from .client import TendersClientSync
from time import time
from gevent import spawn, sleep, idle
from gevent.queue import Queue, Empty
from requests.exceptions import ConnectionError
from openprocurement_client.exceptions import (
    RequestFailed,
    PreconditionFailed,
    ResourceNotFound
)

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

logger = logging.getLogger(__name__)


def get_response(client, params):
    response_fail = True
    sleep_interval = 0.2
    while response_fail:
        try:
            start = time()
            response = client.sync_tenders(params)
            end = time() - start
            logger.debug(
                'Request duration {} sec'.format(end),
                extra={'FEEDER_REQUEST_DURATION': end * 1000})
            response_fail = False
        except PreconditionFailed as e:
            logger.error('PreconditionFailed: {}'.format(e.message),
                         extra={'MESSAGE_ID': 'precondition_failed'})
            continue
        except ConnectionError as e:
            logger.error('ConnectionError: {}'.format(e.message),
                         extra={'MESSAGE_ID': 'connection_error'})
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            logger.debug(
                'Client sleeping after ConnectionError {} sec.'.format(
                    sleep_interval))
            sleep(sleep_interval)
            continue
        except RequestFailed as e:
            logger.error('Request failed. Status code: {}'.format(
                e.status_code), extra={'MESSAGE_ID': 'request_failed'})
            if e.status_code == 429:
                if sleep_interval > 120:
                    raise e
                logger.debug(
                    'Client sleeping after RequestFailed {} sec.'.format(
                        sleep_interval))
                sleep_interval = sleep_interval * 2
                sleep(sleep_interval)
                continue
        except ResourceNotFound as e:
            logger.error('Resource not found: {}'.format(e.message),
                         extra={'MESSAGE_ID': 'resource_not_found'})
            logger.debug('Clear offset and client cookies.')
            client.session.cookies.clear()
            del params['offset']
            continue
        except Exception as e:
            logger.error('Exception: {}'.format(e.message),
                         extra={'MESSAGE_ID': 'exceptions'})
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            logger.debug(
                'Client sleeping after Exception: {}, {} sec.'.format(
                    e.message, sleep_interval))
            sleep(sleep_interval)
            continue
    return response


class ResourceFeeder(object):
    idle = idle

    def __init__(self, host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
                 key=DEFAULT_API_KEY, resource='tenders',
                 extra_params=DEFAULT_API_EXTRA_PARAMS,
                 retrievers_params=DEFAULT_RETRIEVERS_PARAMS, adaptive=False):
        super(ResourceFeeder, self).__init__()
        logger.info('Init Resource Feeder...')
        self.host = host
        self.version = version
        self.key = key
        self.resource = resource
        self.adaptive = adaptive

        self.extra_params = extra_params
        self.retrievers_params = retrievers_params
        self.queue = Queue(maxsize=retrievers_params['queue_size'])

    def init_api_clients(self):
        logger.debug('Init forward and backward clients...')
        self.backward_params = {'descending': True, 'feed': 'changes'}
        self.backward_params.update(self.extra_params)
        self.forward_params = {'feed': 'changes'}
        self.forward_params.update(self.extra_params)
        self.forward_client = TendersClientSync(
            self.key, resource=self.resource, host_url=self.host,
            api_version=self.version)
        self.backward_client = TendersClientSync(
            self.key, resource=self.resource, host_url=self.host,
            api_version=self.version)
        self.cookies = self.forward_client.session.cookies =\
            self.backward_client.session.cookies

    def handle_response_data(self, data):
        for tender in data:
            # self.idle()
            self.queue.put(tender)

    def start_sync(self):
        # self.init_api_clients()
        logger.info('Start sync...')

        response = self.backward_client.sync_tenders(self.backward_params)

        self.handle_response_data(response.data)

        self.backward_params['offset'] = response.next_page.offset
        self.forward_params['offset'] = response.prev_page.offset

        self.backward_worker = spawn(self.retriever_backward)
        self.forward_worker = spawn(self.retriever_forward)

    def restart_sync(self):
        """
        Restart retrieving from Openprocurement API.
        """

        logger.info('Restart workers')
        self.forward_worker.kill()
        self.backward_worker.kill()
        self.init_api_clients()
        self.start_sync()

    def get_resource_items(self):
        """
        Prepare iterator for retrieving from Openprocurement API.

        :param:
            host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
            version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
            key(str): Access key of broker in Openprocurement API. Defaults is DEFAULT_API_KEY
                (Empty string)
            extra_params(dict): Extra params of query

        :returns:
            iterator of tender_object (Munch): object derived from the list of tenders

        """
        self.init_api_clients()
        self.start_sync()
        check_down_worker = True
        while True:
            if check_down_worker and self.backward_worker.ready():
                if self.backward_worker.value == 0:
                    logger.info('Stop check backward worker')
                    check_down_worker = False
                else:
                    self.restart_sync()
                    check_down_worker = True
            if self.forward_worker.ready():
                self.restart_sync()
                check_down_worker = True
            while not self.queue.empty():
                logger.debug(
                    'Feeder queue size: {}'.format(self.queue.qsize()),
                    extra={'FEEDER_QUEUE_SIZE': self.queue.qsize()})
                logger.debug('Yield resource item', extra={'MESSAGE_ID': 'feeder_yield'})
                yield self.queue.get()
            logger.debug(
                'Feeder queue size: {}'.format(self.queue.qsize()),
                extra={'FEEDER_QUEUE_SIZE': self.queue.qsize()})
            try:
                self.queue.peek(block=True, timeout=0.1)
            except Empty:
                pass

    def feeder(self):
        """
        Prepare iterator for retrieving from Openprocurement API.

        :param:
            host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
            version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
            key(str): Access key of broker in Openprocurement API. Defaults is DEFAULT_API_KEY
                (Empty string)
            extra_params(dict): Extra params of query

        :returns:
            iterator of tender_object (Munch): object derived from the list of tenders

        """
        self.init_api_clients()
        self.start_sync()
        check_down_worker = True
        while 1:
            if check_down_worker and self.backward_worker.ready():
                if self.backward_worker.value == 0:
                    logger.info('Stop check backward worker')
                    check_down_worker = False
                else:
                    self.restart_sync()
                    check_down_worker = True
            if self.forward_worker.ready():
                self.restart_sync()
                check_down_worker = True
            logger.debug('Feeder queue size {} items'.format(
                self.queue.qsize()),
                extra={'FEEDER_QUEUE_SIZE': self.queue.qsize()})
            sleep(2)

    def run_feeder(self):
        spawn(self.feeder)
        return self.queue

    def retriever_backward(self):
        logger.info('Backward: Start worker')
        response = get_response(self.backward_client, self.backward_params)
        logger.debug('Backward response length {} items'.format(
            len(response.data)),
            extra={'BACKWARD_RESPONSE_LENGTH': len(response.data)})
        if self.cookies != self.backward_client.session.cookies:
            raise Exception('LB Server mismatch')
        while response.data:
            logger.debug('Backward: Start process data.')
            self.handle_response_data(response.data)
            self.backward_params['offset'] = response.next_page.offset
            self.log_retriever_state(
                'Backward', self.backward_client, self.backward_params)
            logger.debug('Backward: Start process request.')
            response = get_response(self.backward_client, self.backward_params)
            logger.debug('Backward response length {} items'.format(
                len(response.data)),
                extra={'BACKWARD_RESPONSE_LENGTH': len(response.data)})
            if self.cookies != self.backward_client.session.cookies:
                raise Exception('LB Server mismatch')
            logger.info('Backward: pause between requests {} sec.'.format(
                self.retrievers_params.get('down_requests_sleep', 5)))
            sleep(self.retrievers_params.get('down_requests_sleep', 5))
        logger.info('Backward: finished')
        return 0

    def retriever_forward(self):
        logger.info('Forward: Start worker')
        response = get_response(self.forward_client, self.forward_params)
        logger.debug('Forward response length {} items'.format(
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
                logger.debug('Forward response length {} items'.format(
                    len(response.data)),
                    extra={'FORWARD_RESPONSE_LENGTH': len(response.data)})
                if self.cookies != self.forward_client.session.cookies:
                    raise Exception('LB Server mismatch')
                if len(response.data) != 0:
                    logger.info(
                        'Forward: pause between requests {} sec.'.format(
                            self.retrievers_params.get('up_requests_sleep',
                                                       5.0)))
                    sleep(self.retrievers_params.get('up_requests_sleep', 5.0))
            logger.info('Forward: pause after empty response {} sec.'.format(
                self.retrievers_params.get('up_wait_sleep', 30.0)),
                extra={'FORWARD_WAIT_SLEEP':
                       self.retrievers_params.get('up_wait_sleep', 30.0)})
            sleep(self.retrievers_params.get('up_wait_sleep', 30.0))
            self.forward_params['offset'] = response.next_page.offset
            self.log_retriever_state(
                'Forward', self.forward_client, self.forward_params)
            response = get_response(self.forward_client, self.forward_params)
            logger.debug('Forward response length {} items'.format(
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
        logger.debug('{}: offset {}'.format(name, params.get('offset', '')))
        logger.debug('{}: AWSELB {}'.format(
            name,
            client.session.cookies.get('AWSELB', ' ')
        ))
        logger.debug('{}: SERVER_ID {}'.format(
            name, client.session.cookies.get('SERVER_ID', '')
        ))
        logger.debug('{}: limit {}'.format(name, params.get('limit', '')))


def get_resource_items(host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
                       key=DEFAULT_API_KEY,
                       extra_params=DEFAULT_API_EXTRA_PARAMS,
                       retrievers_params=DEFAULT_RETRIEVERS_PARAMS,
                       resource='tenders'):
    """
    Prepare iterator for retrieving from Openprocurement API.

    :param:
        host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
        version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
        key(str): Access key of broker in Openprocurement API. Defaults is DEFAULT_API_KEY
            (Empty string)
        extra_params(dict): Extra params of query

    :returns:
        iterator of tender_object (Munch): object derived from the list of tenders

    """
    feeder = ResourceFeeder(
        host=host, version=version,
        key=key, extra_params=extra_params,
        retrievers_params=retrievers_params, resource=resource
    )
    return feeder.get_resource_items()


def get_tenders(host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
                key=DEFAULT_API_KEY, extra_params=DEFAULT_API_EXTRA_PARAMS,
                retrievers_params=DEFAULT_RETRIEVERS_PARAMS):
    return get_resource_items(host=host, version=version, key=key,
                              resource='tenders', extra_params=extra_params,
                              retrievers_params=retrievers_params)


if __name__ == '__main__':
    for tender_item in get_tenders():
        print('Tender {0[id]}'.format(tender_item))
