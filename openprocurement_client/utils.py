# -*- coding: utf-8 -*-
from openprocurement_client.client import Client
from openprocurement_client.exceptions import IdNotFound
from time import sleep
import logging
logger = logging.getLogger()


def tenders_feed(client=Client(''), sleep_time=10):
    while True:
        tender_list = True
        while tender_list:
            logger.info("Get next batch")
            tender_list = client.get_tenders()
            for tender in tender_list:
                logger.debug("Return tender {}".format(str(tender)))
                yield tender
        logger.info("Wait to get next batch")
        sleep(sleep_time)


def get_tender_id_by_uaid(ua_id, client=Client(''), descending=True, id_field='tenderID'):
    params = {'offset': '', 'opt_fields': id_field, 'descending': descending}
    tender_list = True
    client._update_params(params)
    while tender_list:
        tender_list = client.get_tenders()
        for tender in tender_list:
            if tender[id_field] == ua_id:
                return tender.id
    raise IdNotFound


def get_tender_by_uaid(ua_id, client=Client('')):
    tender_id = get_tender_id_by_uaid(ua_id, client)
    return client.get_tender(tender_id)
