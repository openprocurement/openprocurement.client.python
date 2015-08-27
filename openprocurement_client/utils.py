# -*- coding: utf-8 -*-
from openprocurement_client.client import Client
import logging
from time import sleep
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
