from gevent import monkey
monkey.patch_all()

import logging
from .client import TendersClientSync
from gevent import spawn, sleep, idle
from gevent.queue import Queue, Empty

DEFAULT_RETRIEVERS_PARAMS = {
    'down_requests_sleep': 5,
    'up_requests_sleep': 1,
    'up_wait_sleep': 30,
    'queue_size': 101
}

DEFAULT_API_HOST = 'https://lb.api-sandbox.openprocurement.org/'
DEFAULT_API_VERSION = '2.3'
DEFAULT_API_KEY = ''
DEFAULT_API_EXTRA_PARAMS = {
    'opt_fields': 'status', 'mode': '_all_'}

logger = logging.getLogger(__name__)


def start_sync(host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
               key=DEFAULT_API_KEY, extra_params=DEFAULT_API_EXTRA_PARAMS,
               retrievers_params=DEFAULT_RETRIEVERS_PARAMS, resource='tenders'):
    """
    Start retrieving from Openprocurement API.

    :param:
        host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
        version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
        key(str): Access key of broker in Openprocurement API. Defaults is DEFAULT_API_KEY (Empty string)
        extra_params(dict): Extra params of query

    :returns:
        queue: Queue which containing objects derived from the list of tenders
        forward_worker: Greenlet of forward worker
        backfard_worker: Greenlet of backfard worker

    """
    forward = TendersClientSync(key, resource=resource, host_url=host, api_version=version)
    backfard = TendersClientSync(key, resource=resource, host_url=host, api_version=version)
    Cookie = forward.headers['Cookie'] = backfard.headers['Cookie']
    backfard_params = {'descending': True, 'feed': 'changes'}
    backfard_params.update(extra_params)
    forward_params = {'feed': 'changes'}
    forward_params.update(extra_params)

    response = backfard.sync_tenders(backfard_params)

    queue = Queue(maxsize=retrievers_params['queue_size'])
    for tender in response.data:
        idle()
        queue.put(tender)
    backfard_params['offset'] = response.next_page.offset
    forward_params['offset'] = response.prev_page.offset

    backfard_worker = spawn(retriever_backward, queue,
                            backfard, Cookie, backfard_params,
                            retrievers_params['down_requests_sleep'])
    forward_worker = spawn(retriever_forward, queue,
                           forward, Cookie, forward_params,
                           retrievers_params['up_requests_sleep'],
                           retrievers_params['up_wait_sleep'])

    return queue, forward_worker, backfard_worker


def restart_sync(up_worker, down_worker, host=DEFAULT_API_HOST,
                 version=DEFAULT_API_VERSION, key=DEFAULT_API_KEY,
                 extra_params=DEFAULT_API_EXTRA_PARAMS,
                 retrievers_params=DEFAULT_RETRIEVERS_PARAMS, resource='tenders'):
    """
    Restart retrieving from Openprocurement API.

    Args:
        forward_worker: Greenlet of forward worker
        backfard_worker: Greenlet of backfard worker

    :param:
        host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
        version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
        key(str): Access key of broker in Openprocurement API. Defaults is DEFAULT_API_KEY (Empty string)
        extra_params(dict): Extra params of query

    :returns:
        queue: Queue which containing objects derived from the list of tenders
        forward_worker: Greenlet of forward worker
        backfard_worker: Greenlet of backfard worker

    """

    logger.info('Restart workers')
    up_worker.kill()
    down_worker.kill()
    return start_sync(host=host, version=version, key=key, resource=resource,
                      extra_params=extra_params)


def get_resource_items(host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
              key=DEFAULT_API_KEY, extra_params=DEFAULT_API_EXTRA_PARAMS,
              retrievers_params=DEFAULT_RETRIEVERS_PARAMS, resource='tenders'):
    """
    Prepare iterator for retrieving from Openprocurement API.

    :param:
        host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
        version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
        key(str): Access key of broker in Openprocurement API. Defaults is DEFAULT_API_KEY (Empty string)
        extra_params(dict): Extra params of query

    :returns:
        iterator of tender_object (Munch): object derived from the list of tenders

    """

    queue, up_worker, down_worker = start_sync(
        host=host, version=version, key=key, extra_params=extra_params,
        retrievers_params=retrievers_params, resource=resource)
    check_down_worker = True
    while 1:
        if check_down_worker and down_worker.ready():
            if down_worker.value == 0:
                logger.info('Stop check backward worker')
                check_down_worker = False
            else:
                queue, up_worker, down_worker = restart_sync(up_worker, down_worker,
                    resource=resource, host=host, version=version, key=key,
                    extra_params=extra_params, retrievers_params=retrievers_params)
                check_down_worker = True
        if up_worker.ready():
            queue, up_worker, down_worker = restart_sync(up_worker, down_worker,
                resource=resource, host=host, version=version, key=key,
                extra_params=extra_params, retrievers_params=retrievers_params)
            check_down_worker = True
        while not queue.empty():
            yield queue.get()
        try:
            queue.peek(block=True, timeout=5)
        except Empty:
            pass


def get_tenders(host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
                key=DEFAULT_API_KEY, extra_params=DEFAULT_API_EXTRA_PARAMS,
                retrievers_params=DEFAULT_RETRIEVERS_PARAMS):
    get_resource_items(host=host, version=version, key=key, resource='tenders',
                       extra_params=extra_params,
                       retrievers_params=retrievers_params)



def retriever_backward(queue, client, origin_cookie, params, requests_sleep):
    logger.info('Backward: Start worker')
    response = client.sync_tenders(params)
    if origin_cookie != client.headers['Cookie']:
        raise Exception('LB Server mismatch')
    while response.data:
        for tender in response.data:
            idle()
            queue.put(tender)
        params['offset'] = response.next_page.offset
        response = client.sync_tenders(params)
        if origin_cookie != client.headers['Cookie']:
            raise Exception('LB Server mismatch')
        logger.info('Backward: pause between requests')
        sleep(requests_sleep)
    logger.info('Backward: finished')
    return 0


def retriever_forward(queue, client, origin_cookie, params, requests_sleep, wait_sleep):
    logger.info('Forward: Start worker')
    response = client.sync_tenders(params)
    if origin_cookie != client.headers['Cookie']:
        raise Exception('LB Server mismatch')
    while 1:
        while response.data:
            for tender in response.data:
                idle()
                queue.put(tender)
            params['offset'] = response.next_page.offset
            response = client.sync_tenders(params)
            if origin_cookie != client.headers['Cookie']:
                raise Exception('LB Server mismatch')
            if len(response.data) != 0:
                logger.info('Forward: pause between requests')
                sleep(requests_sleep)

        logger.info('Forward: pause after empty response')
        sleep(wait_sleep)

        params['offset'] = response.next_page.offset
        response = client.sync_tenders(params)
        if origin_cookie != client.headers['Cookie']:
            raise Exception('LB Server mismatch')

    return 1

if __name__ == '__main__':
    for tender_item in get_tenders():
        print 'Tender {0[id]}'.format(tender_item)
