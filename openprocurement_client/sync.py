from gevent import monkey
monkey.patch_all()

import logging
from .client import TendersClientSync
from gevent import spawn, sleep, idle
from gevent.queue import Queue, Empty
from requests.exceptions import ConnectionError
from openprocurement_client.exceptions import (
    RequestFailed,
    ResourceNotFound
)

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
               retrievers_params=DEFAULT_RETRIEVERS_PARAMS, resource='tenders',
               adaptive=False):
    """
    Start retrieving from Openprocurement API.

    :param:
        host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
        version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
        key(str): Access key of broker in Openprocurement API. Defaults is
            DEFAULT_API_KEY (Empty string)
        extra_params(dict): Extra params of query

    :returns:
        queue: Queue which containing objects derived from the list of tenders
        forward_worker: Greenlet of forward worker
        backward_worker: Greenlet of backward worker

    """
    forward = TendersClientSync(key, resource=resource, host_url=host, api_version=version)
    backward = TendersClientSync(key, resource=resource, host_url=host, api_version=version)
    Cookie = forward.session.cookies = backward.session.cookies
    backward_params = {'descending': True, 'feed': 'changes'}
    backward_params.update(extra_params)
    forward_params = {'feed': 'changes'}
    forward_params.update(extra_params)

    response = backward.sync_tenders(backward_params)

    queue = Queue(maxsize=retrievers_params['queue_size'])
    for tender in response.data:
        idle()
        queue.put(tender)
    backward_params['offset'] = response.next_page.offset
    forward_params['offset'] = response.prev_page.offset

    backward_worker = spawn(retriever_backward, queue,
                            backward, Cookie, backward_params,
                            retrievers_params['down_requests_sleep'])
    forward_worker = spawn(retriever_forward, queue,
                           forward, Cookie, forward_params,
                           retrievers_params['up_requests_sleep'],
                           retrievers_params['up_wait_sleep'], adaptive=adaptive)

    return queue, forward_worker, backward_worker


def restart_sync(up_worker, down_worker, host=DEFAULT_API_HOST,
                 version=DEFAULT_API_VERSION, key=DEFAULT_API_KEY,
                 extra_params=DEFAULT_API_EXTRA_PARAMS, adaptive=False,
                 retrievers_params=DEFAULT_RETRIEVERS_PARAMS, resource='tenders'):
    """
    Restart retrieving from Openprocurement API.

    Args:
        forward_worker: Greenlet of forward worker
        backward_worker: Greenlet of backward worker

    :param:
        host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
        version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
        key(str): Access key of broker in Openprocurement API. Defaults is
            DEFAULT_API_KEY (Empty string)
        extra_params(dict): Extra params of query

    :returns:
        queue: Queue which containing objects derived from the list of tenders
        forward_worker: Greenlet of forward worker
        backward_worker: Greenlet of backward worker

    """

    logger.info('Restart workers')
    up_worker.kill()
    down_worker.kill()
    return start_sync(host=host, version=version, key=key, resource=resource,
                      extra_params=extra_params, adaptive=adaptive)


def get_resource_items(host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
                       key=DEFAULT_API_KEY, extra_params=DEFAULT_API_EXTRA_PARAMS,
                       retrievers_params=DEFAULT_RETRIEVERS_PARAMS, resource='tenders',
                       adaptive=False):
    """
    Prepare iterator for retrieving from Openprocurement API.

    :param:
        host (str): Url of Openprocurement API. Defaults is DEFAULT_API_HOST
        version (str): Verion of Openprocurement API. Defaults is DEFAULT_API_VERSION
        key(str): Access key of broker in Openprocurement API. Defaults is
            DEFAULT_API_KEY (Empty string)
        extra_params(dict): Extra params of query

    :returns:
        iterator of tender_object (Munch): object derived from the list of tenders

    """

    queue, up_worker, down_worker = start_sync(
        host=host, version=version, key=key, extra_params=extra_params,
        retrievers_params=retrievers_params, resource=resource, adaptive=adaptive)
    check_down_worker = True
    while 1:
        if check_down_worker and down_worker.ready():
            if down_worker.value == 0:
                logger.info('Stop check backward worker')
                check_down_worker = False
            else:
                queue, up_worker, down_worker = restart_sync(
                    up_worker, down_worker, resource=resource, host=host, version=version,
                    key=key, extra_params=extra_params, retrievers_params=retrievers_params,
                    adaptive=adaptive)
                check_down_worker = True
        if up_worker.ready():
            queue, up_worker, down_worker = restart_sync(
                up_worker, down_worker, resource=resource, host=host, version=version,
                key=key, extra_params=extra_params, retrievers_params=retrievers_params,
                adaptive=adaptive)
            check_down_worker = True
        while not queue.empty():
            yield queue.get()
        try:
            queue.peek(block=True, timeout=5)
        except Empty:
            pass


def get_tenders(host=DEFAULT_API_HOST, version=DEFAULT_API_VERSION,
                key=DEFAULT_API_KEY, extra_params=DEFAULT_API_EXTRA_PARAMS,
                retrievers_params=DEFAULT_RETRIEVERS_PARAMS, adaptive=False):
    return get_resource_items(host=host, version=version, key=key,
                              resource='tenders', extra_params=extra_params,
                              retrievers_params=retrievers_params, adaptive=adaptive)


def log_retriever_state(name, client, params):
    logger.debug('{}: offset {}'.format(name, params.get('offset', '')))
    logger.debug('{}: AWSELB {}'.format(
        name, client.session.cookies.get('AWSELB', '')))
    logger.debug('{}: SERVER_ID {}'.format(
        name, client.session.cookies.get('SERVER_ID', '')))
    logger.debug('{}: limit {}'.format(name, params.get('limit', '')))


def get_response(client, params):
    response_fail = True
    sleep_interval = 0.2
    while response_fail:
        try:
            response = client.sync_tenders(params)
            response_fail = False
        except ConnectionError as e:
            logger.error('ConnectionError: {}'.format(e.message))
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            sleep(sleep_interval)
            continue
        except RequestFailed as e:
            logger.error('Request failed. Status code: {}'.format(
                e.status_code))
            if e.status_code == 429:
                if sleep_interval > 120:
                    raise e
                sleep_interval = sleep_interval * 2
                sleep(sleep_interval)
                continue
        except ResourceNotFound as e:
            logger.error('Resource not found: {}'.format(e.message))
            del params['offset']
            continue
        except Exception as e:
            logger.error('Exception: {}'.format(e.message))
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            sleep(sleep_interval)
            continue
    return response


def retriever_backward(queue, client, origin_cookie, params, requests_sleep):
    logger.info('Backward: Start worker')
    response = get_response(client, params)
    if origin_cookie != client.session.cookies:
        raise Exception('LB Server mismatch')
    while response.data:
        for tender in response.data:
            idle()
            queue.put(tender)
        params['offset'] = response.next_page.offset
        log_retriever_state('Backward', client, params)
        response = get_response(client, params)
        if origin_cookie != client.session.cookies:
            raise Exception('LB Server mismatch')
        logger.info('Backward: pause between requests')
        sleep(requests_sleep)
    logger.info('Backward: finished')
    return 0


def retriever_forward(queue, client, origin_cookie, params, requests_sleep, wait_sleep,
                      adaptive=False):
    logger.info('Forward: Start worker')
    max_wait_sleep = wait_sleep
    response = get_response(client, params)
    if origin_cookie != client.session.cookies:
        raise Exception('LB Server mismatch')
    while 1:
        while response.data:
            for tender in response.data:
                idle()
                queue.put(tender)
            params['offset'] = response.next_page.offset
            log_retriever_state('Forward', client, params)
            response = get_response(client, params)
            if origin_cookie != client.session.cookies:
                raise Exception('LB Server mismatch')
            if len(response.data) != 0:
                logger.info('Forward: pause between requests')
                sleep(requests_sleep)
        logger.info('Forward: pause {} sec. after empty response'.format(wait_sleep))
        sleep(wait_sleep)
        params['offset'] = response.next_page.offset
        log_retriever_state('Forward', client, params)
        response = get_response(client, params)
        if adaptive:
            if len(response.data) != 0 and wait_sleep > 1:
                wait_sleep -= 1
            else:
                if wait_sleep < max_wait_sleep:
                    wait_sleep += 1
        if origin_cookie != client.session.cookies:
            raise Exception('LB Server mismatch')

    return 1


if __name__ == '__main__':
    for tender_item in get_tenders():
        print 'Tender {0[id]}'.format(tender_item)
