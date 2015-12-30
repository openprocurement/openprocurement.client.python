from gevent import monkey; monkey.patch_all()
from gevent.pywsgi import WSGIServer
from bottle import Bottle
from StringIO import StringIO
from collections import Iterable
from simplejson import loads, load
from munch import munchify
import unittest
from openprocurement_client import client
from openprocurement_client.tests._server import (tender_partition, location_error,
                                                 setup_routing, ROOT)


HOST_URL = "http://localhost:20602"
API_KEY = 'e9c3ccb8e8124f26941d5f9639a4ebc3'
API_VERSION = '0.10'

TEST_KEYS = munchify({
    "tender_id": '823d50b3236247adad28a5a66f74db42',
    "empty_tender": 'f3849ade33534174b8402579152a5f41',
    "question_id": '615ff8be8eba4a81b300036d6bec991c',
    "lot_id": '563ef5d999f34d36a5a0e4e4d91d7be1',
    "bid_id": 'f7fc1212f9f140bba5c4e3cd4f2b62d9',
    "bid_document_id":"ff001412c60c4164a0f57101e4eaf8aa",
    "award_id": '7054491a5e514699a56e44d32e23edf7',
    "document_id": '330822cbbd724671a1d2ff7c3a51dd52',
    "new_document_id": '12345678123456781234567812345678',
    "error_id": '111a11a1111111aaa11111a1a1a111a1'
})


class ViewerTestCase(unittest.TestCase):
    """"""
    def setUp(self):
        #self._testMethodName
        self.app = Bottle()
        setup_routing(self.app)
        self.server = WSGIServer(('localhost', 20602), self.app, log=None)
        self.server.start()

        self.client = client.Client('', host_url=HOST_URL, api_version=API_VERSION)

        with open(ROOT + 'tenders.json') as tenders:
            self.tenders = munchify(load(tenders))
        with open(ROOT + TEST_KEYS.tender_id + '.json') as tender:
            self.tender = munchify(load(tender))

    def tearDown(self):
        self.server.stop()


    def test_get_tenders(self):
        setup_routing(self.app, routs=["tenders"])
        tenders = self.client.get_tenders()
        self.assertIsInstance(tenders, Iterable)
        self.assertEqual(tenders, self.tenders.data)

    def test_get_tender(self):
        setup_routing(self.app, routs=["tender"])
        tender = self.client.get_tender(TEST_KEYS.tender_id)
        self.assertEqual(tender, self.tender)

    def test_get_tender_location_error(self):
        setup_routing(self.app, routs=["tender"])
        tender = self.client.get_tender(TEST_KEYS.error_id)
        self.assertEqual(tender, munchify(loads(location_error('tender'))))

    def test_offset_error(self):
        setup_routing(self.app, routs=['offset_error'])
        tenders = self.client.get_tenders()
        self.assertIsInstance(tenders, Iterable)
        self.assertEqual(tenders, self.tenders.data)



class UserTestCase(unittest.TestCase):
    """"""
    def setUp(self):
        #self._testMethodName
        self.app = Bottle()

        setup_routing(self.app)
        self.server = WSGIServer(('localhost', 20602), self.app, log=None)
        self.server.start()
        self.client = client.Client(API_KEY,  host_url=HOST_URL, api_version=API_VERSION)

        with open(ROOT + TEST_KEYS.tender_id + '.json') as tender:
            self.tender = munchify(load(tender))
            self.tender.update({'access':{"token": API_KEY}})
        with open(ROOT + TEST_KEYS.empty_tender + '.json') as tender:
            self.empty_tender = munchify(load(tender))
            self.empty_tender.update({'access':{"token": API_KEY}})

    def tearDown(self):
        self.server.stop()


    ###########################################################################
    #             GET ITEMS LIST TEST
    ###########################################################################

    def test_get_questions(self):
        setup_routing(self.app, routs=["tender_subpage"])
        questions = munchify({'data': self.tender['data'].get('questions', [])})
        self.assertEqual(self.client.get_questions(self.tender), questions)

    def test_get_documents(self):
        setup_routing(self.app, routs=["tender_subpage"])
        documents = munchify({'data': self.tender['data'].get('documents', [])})
        self.assertEqual(self.client.get_documents(self.tender), documents)

    def test_get_awards(self):
        setup_routing(self.app, routs=["tender_subpage"])
        awards = munchify({'data': self.tender['data'].get('awards', [])})
        self.assertEqual(self.client.get_awards(self.tender), awards)

    def test_get_lots(self):
        setup_routing(self.app, routs=["tender_subpage"])
        lots = munchify({'data': self.tender['data'].get('lots', [])})
        self.assertEqual(self.client.get_lots(self.tender), lots)

    ###########################################################################
    #             CREATE ITEM TEST
    ###########################################################################

    def test_create_tender(self):
        setup_routing(self.app, routs=["tender_create"])
        tender = munchify({'data': 'tender'})
        self.client.create_tender(self.tender)

    def test_create_question(self):
        setup_routing(self.app, routs=["tender_subpage_item_create"])
        question = munchify({'data': 'question'})
        self.assertEqual(self.client.create_question(self.tender, question), question)

    def test_create_bid(self):
        setup_routing(self.app, routs=["tender_subpage_item_create"])
        bid = munchify({'data': 'bid'})
        self.assertEqual(self.client.create_bid(self.tender, bid), bid)

    def test_create_lot(self):
        setup_routing(self.app, routs=["tender_subpage_item_create"])
        lot = munchify({'data': 'lot'})
        self.assertEqual(self.client.create_lot(self.tender, lot), lot)

    ###########################################################################
    #             GET ITEM TEST
    ###########################################################################


    def test_get_question(self):
        setup_routing(self.app, routs=["tender_subpage_item"])
        questions = tender_partition(TEST_KEYS.tender_id, part="questions")
        for question in questions:
            if question['id'] == TEST_KEYS.question_id:
                question_ = munchify({"data": question})
                break
        question = self.client.get_question(self.tender, question_id=TEST_KEYS.question_id)
        self.assertEqual(question, question_)

    def test_get_lot(self):
        setup_routing(self.app, routs=["tender_subpage_item"])
        lots = tender_partition(TEST_KEYS.tender_id, part="lots")
        for lot in lots:
            if lot['id'] == TEST_KEYS.lot_id:
                lot_ = munchify({"data": lot})
                break
        lot = self.client.get_lot(self.tender, lot_id=TEST_KEYS.lot_id)
        self.assertEqual(lot, lot_)

    def test_get_bid(self):
        setup_routing(self.app, routs=["tender_subpage_item"])
        bids = tender_partition(TEST_KEYS.tender_id, part="bids")
        for bid in bids:
            if bid['id'] == TEST_KEYS.bid_id:
                bid_ = munchify({"data": bid})
                break
        bid = self.client.get_bid(self.tender, bid_id=TEST_KEYS.bid_id, access_token=API_KEY)
        self.assertEqual(bid , bid_)

    def test_get_location_error(self):
        setup_routing(self.app, routs=["tender_subpage_item"])
        self.assertEqual(self.client.get_question(self.empty_tender, question_id=TEST_KEYS.question_id),
                         munchify(loads(location_error('questions'))))
        self.assertEqual(self.client.get_lot(self.empty_tender, lot_id=TEST_KEYS.lot_id),
                         munchify(loads(location_error('lots'))))
        self.assertEqual(self.client.get_bid(self.empty_tender, bid_id=TEST_KEYS.bid_id, access_token=API_KEY),
                         munchify(loads(location_error('bids'))))


    ###########################################################################
    #             PATCH ITEM TEST
    ###########################################################################

    def test_patch_tender(self):
        setup_routing(self.app, routs=["tender_patch"])
        self.tender.data.description = 'test_patch_tender'
        patched_tender = self.client.patch_tender(self.tender)
        self.assertEqual(patched_tender.data.id, self.tender.data.id)
        self.assertEqual(patched_tender.data.description, self.tender.data.description)

    def test_patch_question(self):
        setup_routing(self.app, routs=["tender_subpage_item_patch"])
        question = munchify({"data": {"id": TEST_KEYS.question_id, "description": "test_patch_question"}})
        patched_question = self.client.patch_question(self.tender, question)
        self.assertEqual(patched_question.data.id, question.data.id)
        self.assertEqual(patched_question.data.description, question.data.description)

    def test_patch_bid(self):
        setup_routing(self.app, routs=["tender_subpage_item_patch"])
        bid = munchify({"data": {"id": TEST_KEYS.bid_id, "description": "test_patch_bid"}})
        patched_bid = self.client.patch_bid(self.tender, bid)
        self.assertEqual(patched_bid.data.id, bid.data.id)
        self.assertEqual(patched_bid.data.description, bid.data.description)

    def test_patch_award(self):
        setup_routing(self.app, routs=["tender_subpage_item_patch"])
        award = munchify({"data": {"id": TEST_KEYS.award_id, "description": "test_patch_award"}})
        patched_award =self.client.patch_award(self.tender, award)
        self.assertEqual(patched_award.data.id, award.data.id)
        self.assertEqual(patched_award.data.description, award.data.description)

    def test_patch_lot(self):
        setup_routing(self.app, routs=["tender_subpage_item_patch"])
        lot = munchify({"data": {"id": TEST_KEYS.lot_id, "description": "test_patch_lot"}})
        patched_lot = self.client.patch_lot(self.tender, lot)
        self.assertEqual(patched_lot.data.id, lot.data.id)
        self.assertEqual(patched_lot.data.description, lot.data.description)

    def test_patch_document(self):
        setup_routing(self.app, routs=["tender_subpage_item_patch"])
        document = munchify({"data": {"id": TEST_KEYS.document_id, "title": "test_patch_document.txt"}})
        patched_document = self.client.patch_document(self.tender, document)
        self.assertEqual(patched_document.data.id, document.data.id)
        self.assertEqual(patched_document.data.title, document.data.title)

    def test_patch_location_error(self):
        setup_routing(self.app, routs=["tender_subpage_item_patch"])
        error = munchify({"data": {"id": TEST_KEYS.error_id}, "access": {"token": API_KEY}})
        self.assertEqual(self.client.patch_question(self.empty_tender, error),
                         munchify(loads(location_error('questions'))))
        self.assertEqual(self.client.patch_bid(self.empty_tender, error),
                         munchify(loads(location_error('bids'))))
        self.assertEqual(self.client.patch_award(self.empty_tender, error),
                         munchify(loads(location_error('awards'))))
        self.assertEqual(self.client.patch_lot(self.empty_tender, error),
                         munchify(loads(location_error('lots'))))
        self.assertEqual(self.client.patch_document(self.empty_tender, error),
                         munchify(loads(location_error('documents'))))

    ###########################################################################
    #             DOCUMENTS FILE TEST
    ###########################################################################

    def test_get_file(self):
        setup_routing(self.app, routs=["redirect","download"])
        file_name = 'test_document.txt'
        with open(ROOT + file_name) as local_file:
            test_file_data = local_file.read()
        url = HOST_URL + '/redirect/' + file_name
        doc = self.client.get_file(self.tender, url, API_KEY)
        self.assertEqual(test_file_data, doc[0])
        self.assertEqual(file_name, doc[1])

    def test_get_file_dont_exist_error(self):
        setup_routing(self.app, routs=["redirect","download"])
        file_name = 'error.txt'
        url = HOST_URL + '/redirect/' + file_name
        self.assertRaises(client.InvalidResponse, self.client.get_file, self.tender, url, API_KEY)

    def test_get_file_no_token_error(self):
        setup_routing(self.app, routs=["redirect","download"])
        file_name = 'test_document.txt'
        url = HOST_URL + '/redirect/' + file_name
        self.assertRaises(client.NoToken, self.client.get_file, self.tender, url, '')

    def test_upload_tender_document(self):
        setup_routing(self.app, routs=["tender_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_document(file_, self.tender)
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_KEYS.new_document_id)
        file_.close()

    def test_upload_tender_document_path(self):
        setup_routing(self.app, routs=["tender_document_create"])
        file_name = "test_document.txt"
        file_path = ROOT + file_name
        doc = self.client.upload_document(file_path, self.tender)
        self.assertEqual(doc.data.title, file_name)
        self.assertEqual(doc.data.id, TEST_KEYS.new_document_id)

    def test_upload_bid_document(self):
        setup_routing(self.app, routs=["tender_subpage_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_bid_document(file_, self.tender, TEST_KEYS.bid_id)
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_KEYS.new_document_id)
        file_.close()

    def test_upload_document_type_error(self):
        setup_routing(self.app, routs=["tender_document_create"])
        self.assertRaises(TypeError,self.client.upload_document, (object, self.tender))

    def test_update_bid_document(self):
        setup_routing(self.app, routs=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.update_bid_document(file_, self.tender, TEST_KEYS.bid_id, TEST_KEYS.bid_document_id)
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_KEYS.bid_document_id)
        file_.close()



    ###########################################################################
    #             DELETE ITEMS LIST TEST
    ###########################################################################


    def test_delete_bid(self):
        setup_routing(self.app, routs=["tender_subpage_item_delete"])
        bid_id = tender_partition(TEST_KEYS.tender_id, part="bids")[0]['id']
        deleted_bid = self.client.delete_bid(self.tender, bid_id, API_KEY)
        self.assertFalse(deleted_bid)

    def test_delete_lot(self):
        setup_routing(self.app, routs=["tender_subpage_item_delete"])
        lot_id = tender_partition(TEST_KEYS.tender_id, part="lots")[0]['id']
        deleted_lot = self.client.delete_lot(self.tender, lot_id)
        self.assertFalse(deleted_lot)

    def test_delete_location_error(self):
        setup_routing(self.app, routs=["tender_subpage_item_delete"])
        self.assertEqual(self.client.delete_bid(self.empty_tender, TEST_KEYS.error_id, API_KEY),
                         munchify(loads(location_error('bids'))))
        self.assertEqual(self.client.delete_lot(self.empty_tender, TEST_KEYS.error_id),
                         munchify(loads(location_error('lots'))))



if __name__ == '__main__':
    unittest.main()
