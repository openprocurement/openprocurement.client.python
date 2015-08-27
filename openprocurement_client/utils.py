# -*- coding: utf-8 -*-
from openprocurement_client.client import Client
import logging
from time import sleep
logger = logging.getLogger()


def tenders_feed(client=Client(''), sleep_time=10):
    while True:
        tender_list = True
        #Витягнення тендерів
        while tender_list:
            #logger.info("Get next batch")
            tender_list = client.get_tenders()
            for tender in tender_list:
                yield tender
                #write_to_db(tender, tenders_folder)
        sleep(sleep_time)
