from gevent import monkey, sleep
monkey.patch_all()

import logging
from openprocurement_client.client import TendersClientSync
from gevent import spawn
from gevent.queue import Queue, Full


logger = logging.getLogger(__name__)


def start_sync(api_host, api_version, api_key='', **params):
    """
    Start retrieving from Openprocurement API.
    :param:
        api_host (str): Url of Openprocurement API.
        api_version (str): Verion of Openprocurement API.
        api_key(str): Access api_key of broker in Openprocurement API. Default is empty string.
    :returns:
        queue: Queue which containing objects derived from the list of tenders
        forward_worker: Greenlet of forward worker
        backward_worker: Greenlet of backward worker
    """
    queue_size = params.get('retrievers_queue_size', 500)
    extra_params = params.get('api_extra_params', {})
    on_full_queue_delay = params.get('on_full_queue_delay', 5)

    forward = TendersClientSync(api_key, api_host, api_version)
    backward = TendersClientSync(api_key, api_host, api_version)

    Cookie = forward.headers['Cookie'] = backward.headers['Cookie']
    backward_params = {'descending': True, 'feed': 'changes'}
    backward_params.update(extra_params)
    forward_params = {'feed': 'changes'}
    forward_params.update(extra_params)

    response = backward.sync_tenders(backward_params)

    queue = Queue(queue_size)
    for tender in response.data:
        try:
            queue.put(tender)
        except Full:
            while queue.full():
                sleep(on_full_queue_delay)
            queue.put(tender)
    backward_params['offset'] = response.next_page.offset
    forward_params['offset'] = response.prev_page.offset

    backward_worker = spawn(
        retriever_backward, queue, backward, Cookie, backward_params, **params)

    forward_worker = spawn(
        retriever_forward, queue, forward, Cookie, forward_params, **params)

    return queue, forward_worker, backward_worker


def restart_sync(forward, backward, api_host,
                 api_version, api_key='', **params):
    """
    Restart retrieving from Openprocurement API.
    Args:
        forward_worker: Greenlet of forward worker
        backward_worker: Greenlet of backward worker
    :param:
        host (str): Url of Openprocurement API.
        api_version (str): Verion of Openprocurement API.
        api_key(str): Access api_key of broker in Openprocurement API.
    :returns:
        queue: Queue which containing objects derived from the list of tenders
        forward_worker: Greenlet of forward worker
        backward_worker: Greenlet of backward worker
    """

    logger.info('Restart workers')
    for worker in [forward, backward]:
        worker.kill()
    return start_sync(
        api_host=api_host, api_version=api_version, api_key=api_key, **params)


def get_tenders(api_host, api_version, api_key, api_extra_params, **params):
    """
    Prepare iterator for retrieving from Openprocurement API.
    :param:
        api_host (str): Url of Openprocurement API.
        api_version (str): Verion of Openprocurement API.
        api_key(str): Access api_key of broker in Openprocurement API.
    :returns:
        iterator of tender_object (Munch): object derived from the list of tenders
    """
    retrievers_empty_queue_delay = params.get('retrievers_empty_queue_delay', 5)

    queue, up_worker, down_worker = start_sync(
        api_host=api_host,
        api_version=api_version,
        api_key=api_key,
        api_extra_params=api_extra_params,
        **params
    )

    check_down_worker = True

    while 1:
        if check_down_worker and down_worker.ready():
            if down_worker.value == 0:
                logger.info('Stop check backward worker')
                check_down_worker = False
            else:
                queue, up_worker, down_worker = restart_sync(
                    up_worker, down_worker,
                    api_host=api_host,
                    api_version=api_version,
                    api_key=api_key,
                    **params
                )

                check_down_worker = True
        if up_worker.ready():
            queue, up_worker, down_worker = restart_sync(
                up_worker, down_worker,
                api_host=api_host,
                api_version=api_version,
                api_key=api_key,
                **params
            )

            check_down_worker = True
        while not queue.empty():
            yield queue.get()

        sleep(retrievers_empty_queue_delay)


def retriever_backward(queue, client, origin_cookie, client_params, **params):
    logger.info('Backward: Start worker')
    retriever_down_requests_delay = params.get('retriever_down_requests_delay', 5)
    on_full_queue_delay = params.get('on_full_queue_delay', 5)

    response = client.sync_tenders(client_params)
    if origin_cookie != client.headers['Cookie']:
        raise Exception('LB Server mismatch')
    while response.data:
        for tender in response.data:
            try:
                queue.put(tender)
            except Full:
                while queue.full():
                    sleep(on_full_queue_delay)
                queue.put(tender)
        client_params['offset'] = response.next_page.offset
        response = client.sync_tenders(client_params)
        if origin_cookie != client.headers['Cookie']:
            raise Exception('LB Server mismatch')
        logger.debug('Backward: pause between requests')
        sleep(retriever_down_requests_delay)
    logger.info('Backward: finished')
    return 0


def retriever_forward(queue, client, origin_cookie, client_params, **params):
    logger.info('Forward: Start worker')
    retriever_up_requests_delay = params.get('retriever_up_requests_delay', 1)
    retriever_up_wait_delay = params.get('retriever_up_wait_delay', 30)
    on_full_queue_delay = params.get('on_full_queue_delay', 5)

    response = client.sync_tenders(client_params)
    if origin_cookie != client.headers['Cookie']:
        raise Exception('LB Server mismatch')
    while 1:
        while response.data:
            for tender in response.data:
                try:
                    queue.put(tender)
                except Full:
                    while queue.full():
                        sleep(on_full_queue_delay)
                    queue.put(tender)
            client_params['offset'] = response.next_page.offset
            response = client.sync_tenders(client_params)
            if origin_cookie != client.headers['Cookie']:
                raise Exception('LB Server mismatch')
            if len(response.data) != 0:
                logger.debug('Forward: pause between requests')
                sleep(retriever_up_requests_delay)

        logger.debug('Forward: pause after empty response')
        sleep(retriever_up_wait_delay)

        params['offset'] = response.next_page.offset
        response = client.sync_tenders(client_params)
        if origin_cookie != client.headers['Cookie']:
            raise Exception('LB Server mismatch')

    return 1

