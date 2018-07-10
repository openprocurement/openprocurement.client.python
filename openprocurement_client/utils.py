# -*- coding: utf-8 -*-
import logging
from functools import wraps
from io import FileIO
from os import path
from time import sleep, time

from openprocurement_client.exceptions import (IdNotFound, PreconditionFailed,
                                               RequestFailed, ResourceNotFound)
from requests.exceptions import ConnectionError

LOGGER = logging.getLogger()


# Using FileIO here instead of open()
# to be able to override the filename
# which is later used when uploading the file.
#
# Explanation:
#
# 1) requests reads the filename
# from "name" attribute of a file-like object,
# there is no other way to specify a filename;
#
# 2) The attribute may contain the full path to file,
# which does not work well as a filename;
#
# 3) The attribute is readonly when using open(),
# unlike FileIO object.


def verify_file(fn):
    """ Decorator for upload or update document methods"""
    @wraps(fn)
    def wrapper(self, file_, *args, **kwargs):
        if isinstance(file_, basestring):
            file_ = FileIO(file_, 'rb')
            file_.name = path.basename(file_.name)
        if hasattr(file_, 'read'):
            # A file-like object must have 'read' method
            output = fn(self, file_, *args, **kwargs)
            file_.close()
            return output
        else:
            try:
                file_.close()
            except AttributeError:
                pass
            raise TypeError(
                'Expected either a string containing a path to file or '
                'a file-like object, got {}'.format(type(file_))
            )
    return wrapper


def tenders_feed(client, sleep_time=10):
    while True:
        tender_list = True
        while tender_list:
            LOGGER.info("Get next batch")
            tender_list = client.get_tenders()
            for tender in tender_list:
                LOGGER.debug("Return tender {}".format(str(tender)))
                yield tender
        LOGGER.info("Wait to get next batch")
        sleep(sleep_time)


def get_tender_id_by_uaid(ua_id, client, descending=True, id_field='tenderID'):
    params = {'offset': '', 'opt_fields': id_field, 'descending': descending}
    tender_list = True
    client._update_params(params)
    while tender_list:
        tender_list = client.get_tenders()
        for tender in tender_list:
            if tender[id_field] == ua_id:
                return tender.id
    raise IdNotFound


def get_tender_by_uaid(ua_id, client):
    tender_id = get_tender_id_by_uaid(ua_id, client)
    return client.get_tender(tender_id)


def get_contract_id_by_uaid(ua_id, client, descending=True, id_field='contractID'):
    params = {'offset': '', 'opt_fields': id_field, 'descending': descending}
    contract_list = True
    client._update_params(params)
    while contract_list:
        contract_list = client.get_contracts()
        for contract in contract_list:
            if contract[id_field] == ua_id:
                return contract.id
    raise IdNotFound


def get_plan_id_by_uaid(ua_id, client, descending=True, id_field='planID'):
    params = {'offset': '', 'opt_fields': id_field, 'descending': descending}
    tender_list = True
    client._update_params(params)
    while tender_list:
        tender_list = client.get_plans()
        for tender in tender_list:
            if tender[id_field] == ua_id:
                return tender.id
    raise IdNotFound


def get_monitoring_id_by_uaid(ua_id, client, descending=True, id_field='monitoring_id'):
    params = {'offset': '', 'opt_fields': id_field, 'descending': descending}
    monitoring_list = True
    client._update_params(params)
    while monitoring_list:
        monitoring_list = client.get_monitorings()
        for monitoring in monitoring_list:
            if monitoring[id_field] == ua_id:
                return monitoring.id
    raise IdNotFound


def get_response(client, params):
    response_fail = True
    sleep_interval = 0.2
    while response_fail:
        try:
            start = time()
            response = client.sync_resource_items(params)
            end = time() - start
            LOGGER.debug('Request duration {} sec'.format(end), extra={'FEEDER_REQUEST_DURATION': end * 1000})
            response_fail = False
        except PreconditionFailed as e:
            LOGGER.error('PreconditionFailed: {}'.format(e.message), extra={'MESSAGE_ID': 'precondition_failed'})
            continue
        except ConnectionError as e:
            LOGGER.error('ConnectionError: {}'.format(e.message), extra={'MESSAGE_ID': 'connection_error'})
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            LOGGER.debug('Client sleeping after ConnectionError {} sec.'.format(sleep_interval))
            sleep(sleep_interval)
            continue
        except RequestFailed as e:
            LOGGER.error('RequestFailed: Status code: {}'.format(e.status_code),
                         extra={'MESSAGE_ID': 'request_failed'})
            if e.status_code == 429:
                if sleep_interval > 120:
                    raise e
                LOGGER.debug('Client sleeping after RequestFailed {} sec.'.format(sleep_interval))
                sleep_interval = sleep_interval * 2
                sleep(sleep_interval)
                continue
        except ResourceNotFound as e:
            LOGGER.error('Resource not found: {}'.format(e.message), extra={'MESSAGE_ID': 'resource_not_found'})
            LOGGER.debug('Clear offset and client cookies.')
            client.session.cookies.clear()
            del params['offset']
            continue
        except Exception as e:
            LOGGER.error('Exception: {}'.format(repr(e)), extra={'MESSAGE_ID': 'exceptions'})
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            LOGGER.debug('Client sleeping after Exception: {}, {} sec.'.format(e.message, sleep_interval))
            sleep(sleep_interval)
            continue
    return response
