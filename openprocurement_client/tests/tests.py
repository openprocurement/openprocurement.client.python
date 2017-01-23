from __future__ import print_function
from gevent import monkey; monkey.patch_all()
from gevent.pywsgi import WSGIServer
from bottle import Bottle
from StringIO import StringIO
from collections import Iterable
from simplejson import loads, load
from munch import munchify
import sys
import unittest
from openprocurement_client.client import TendersClient
from openprocurement_client.contract import ContractingClient
from openprocurement_client.document_service_client \
    import DocumentServiceClient
from openprocurement_client.exceptions import ResourceNotFound
from openprocurement_client.plan import PlansClient
from openprocurement_client.tests._server import \
    API_KEY, API_VERSION, AUTH_DS_FAKE, DS_HOST_URL, DS_PORT, \
    HOST_URL, location_error,  PORT, ROOT, setup_routing, setup_routing_ds, \
    tender_partition


TEST_TENDER_KEYS = munchify({
    "tender_id": '823d50b3236247adad28a5a66f74db42',
    "empty_tender": 'f3849ade33534174b8402579152a5f41',
    "question_id": '615ff8be8eba4a81b300036d6bec991c',
    "lot_id": '563ef5d999f34d36a5a0e4e4d91d7be1',
    "bid_id": 'f7fc1212f9f140bba5c4e3cd4f2b62d9',
    "bid_document_id":"ff001412c60c4164a0f57101e4eaf8aa",
    "bid_qualification_document_id": "7519d21b32af432396acd6e2c9e18ee5",
    "bid_financial_document_id": "7519d21b32af432396acd6e2c9e18ee5",
    "bid_eligibility_document_id": "7519d21b32af432396acd6e2c9e18ee5",
    "award_id": '7054491a5e514699a56e44d32e23edf7',
    "qualification_id": "cec4b82d2708465291fb4af79f8a3e52",
    "document_id": '330822cbbd724671a1d2ff7c3a51dd52',
    "new_document_id": 'jh8LjkJ477kJ6lovWER8HRT839jDs82h',
    "error_id": '111a11a1111111aaa11111a1a1a111a1'
})

TEST_TENDER_KEYS_LIMITED = munchify({
    "tender_id": '668c3156c8cb496fb28359909cde6e96',
    "cancellation_id": "0dd6f9e8cc4f4d1c9c404d842b56d0d7",
    "cancellation_document_id": "1afca9faaf2b4f9489ee264b136371c6",
    "document_id": "330822cbbd724671a1d2ff7c3a51dd52",
    "contract_id": "c65d3526cdc44f75b2457b4489970a7c",
    "complaint_id": "22b086222a7a4bc6a9cc8adeaa91a57f",
    "complaint_document_id": "129f4013b33a45b8bc70699a62a81499"
})

TEST_PLAN_KEYS = munchify({
    "plan_id": '34cebf0e7b474753854b0ef155b4a0f1',
    "error_id": 'xxx111'
})

TEST_CONTRACT_KEYS = munchify({
    "contract_id": '3c0bf3eed3fc4b189103e62b828c599d',
    "new_document_id": 'newid678123456781234567812345678',
    "error_id": 'zzzxxx111'
})


def generate_file_obj(file_name, content):
    file_ = StringIO()
    file_.name = file_name
    file_.write(content)
    file_.seek(0)
    return file_


class BaseTestClass(unittest.TestCase):

    def setting_up(self, client):
        self.app = Bottle()
        setup_routing(self.app)
        self.server = WSGIServer(('localhost', PORT), self.app, log=None)
        try:
            self.server.start()
        except Exception as error:
            print(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2],
                  file=sys.stderr)
            raise error
        ds_client = getattr(self, 'ds_client', None)
        self.client = client('', host_url=HOST_URL, api_version=API_VERSION,
                             ds_client=ds_client)

    @classmethod
    def setting_up_ds(cls):
        cls.app_ds = Bottle()
        cls.server_ds \
            = WSGIServer(('localhost', DS_PORT), cls.app_ds, log=None)
        try:
            cls.server_ds.start()
        except Exception as error:
            print(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2],
                  file=sys.stderr)
            raise error

        cls.ds_client = DocumentServiceClient(host_url=DS_HOST_URL,
                                              auth_ds=AUTH_DS_FAKE)
        # to test units performing file operations outside the DS uncomment
        # following lines:
        # import logging
        # logging.basicConfig()
        # cls.ds_client = None

        setup_routing_ds(cls.app_ds)

    @classmethod
    def setUpClass(cls):
        cls.setting_up_ds()


    @classmethod
    def tearDownClass(cls):
        cls.server_ds.stop()


class ViewerTenderTestCase(BaseTestClass):
    """"""
    def setUp(self):
        self.setting_up(client=TendersClient)

        with open(ROOT + 'tenders.json') as tenders:
            self.tenders = munchify(load(tenders))
        with open(ROOT + TEST_TENDER_KEYS.tender_id + '.json') as tender:
            self.tender = munchify(load(tender))

    def tearDown(self):
        self.server.stop()

    def test_get_tenders(self):
        setup_routing(self.app, routes=["tenders"])
        tenders = self.client.get_tenders()
        self.assertIsInstance(tenders, Iterable)
        self.assertEqual(tenders, self.tenders.data)

    def test_get_tender(self):
        setup_routing(self.app, routes=["tender"])
        tender = self.client.get_tender(TEST_TENDER_KEYS.tender_id)
        self.assertEqual(tender, self.tender)

    def test_get_tender_location_error(self):
        setup_routing(self.app, routes=["tender"])
        tender = self.client.get_tender(TEST_TENDER_KEYS.error_id)
        self.assertEqual(tender, munchify(loads(location_error('tender'))))

    def test_offset_error(self):
        setup_routing(self.app, routes=['offset_error'])
        tenders = self.client.get_tenders()
        self.assertIsInstance(tenders, Iterable)
        self.assertEqual(tenders, self.tenders.data)


class ViewerPlanTestCase(BaseTestClass):
    """"""
    def setUp(self):
        self.setting_up(client=PlansClient)

        with open(ROOT + 'plans.json') as plans:
            self.plans = munchify(load(plans))
        with open(ROOT + 'plan_' + TEST_PLAN_KEYS.plan_id + '.json') as plan:
            self.plan = munchify(load(plan))

    def tearDown(self):
        self.server.stop()

    def test_get_plans(self):
        setup_routing(self.app, routes=["plans"])
        plans = self.client.get_plans()
        self.assertIsInstance(plans, Iterable)
        self.assertEqual(plans, self.plans.data)

    def test_get_plan(self):
        setup_routing(self.app, routes=["plan"])
        plan = self.client.get_plan(TEST_PLAN_KEYS.plan_id)
        self.assertEqual(plan, self.plan)

    def test_get_plan_location_error(self):
        setup_routing(self.app, routes=["plan"])
        tender = self.client.get_plan(TEST_PLAN_KEYS.error_id)
        self.assertEqual(tender, munchify(loads(location_error('plan'))))

    def test_offset_error(self):
        setup_routing(self.app, routes=['plan_offset_error'])
        plans = self.client.get_plans()
        self.assertIsInstance(plans, Iterable)
        self.assertEqual(plans, self.plans.data)


class UserTestCase(BaseTestClass):
    """"""
    def setUp(self):
        #self._testMethodName
        self.setting_up(client=TendersClient)

        with open(ROOT + TEST_TENDER_KEYS.tender_id + '.json') as tender:
            self.tender = munchify(load(tender))
            self.tender.update({'access':{"token": API_KEY}})
        with open(ROOT + TEST_TENDER_KEYS.empty_tender + '.json') as tender:
            self.empty_tender = munchify(load(tender))
            self.empty_tender.update({'access':{"token": API_KEY}})
        with open(ROOT + TEST_TENDER_KEYS_LIMITED.tender_id + '.json') as tender:
            self.limited_tender = munchify(load(tender))
            self.limited_tender.update({'access':{"token": API_KEY}})

    def tearDown(self):
        self.server.stop()


    ###########################################################################
    #             GET ITEMS LIST TEST
    ###########################################################################

    def test_get_questions(self):
        setup_routing(self.app, routes=["tender_subpage"])
        questions = munchify({'data': self.tender['data'].get('questions', [])})
        self.assertEqual(self.client.get_questions(self.tender), questions)

    def test_get_documents(self):
        setup_routing(self.app, routes=["tender_subpage"])
        documents = munchify({'data': self.tender['data'].get('documents', [])})
        self.assertEqual(self.client.get_documents(self.tender), documents)

    def test_get_awards(self):
        setup_routing(self.app, routes=["tender_subpage"])
        awards = munchify({'data': self.tender['data'].get('awards', [])})
        self.assertEqual(self.client.get_awards(self.tender), awards)

    def test_get_lots(self):
        setup_routing(self.app, routes=["tender_subpage"])
        lots = munchify({'data': self.tender['data'].get('lots', [])})
        self.assertEqual(self.client.get_lots(self.tender), lots)

    ###########################################################################
    #             CREATE ITEM TEST
    ###########################################################################

    def test_create_tender(self):
        setup_routing(self.app, routes=["tender_create"])
        tender = munchify({'data': 'tender'})
        self.client.create_tender(self.tender)

    def test_create_question(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        question = munchify({'data': 'question'})
        self.assertEqual(self.client.create_question(self.tender, question), question)

    def test_create_bid(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        bid = munchify({'data': 'bid'})
        self.assertEqual(self.client.create_bid(self.tender, bid), bid)

    def test_create_lot(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        lot = munchify({'data': 'lot'})
        self.assertEqual(self.client.create_lot(self.tender, lot), lot)

    def test_create_award(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        award = munchify({'data': 'award'})
        self.assertEqual(self.client.create_award(self.limited_tender, award), award)

    def test_create_cancellation(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        cancellation = munchify({'data': 'cancellation'})
        self.assertEqual(self.client.create_cancellation(self.limited_tender, cancellation), cancellation)

    def test_create_complaint(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        complaint = munchify({'data': 'complaint'})
        self.assertEqual(self.client.create_complaint(self.limited_tender, complaint), complaint)

    ###########################################################################
    #             GET ITEM TEST
    ###########################################################################

    def test_get_question(self):
        setup_routing(self.app, routes=["tender_subpage_item"])
        questions = tender_partition(TEST_TENDER_KEYS.tender_id, part="questions")
        for question in questions:
            if question['id'] == TEST_TENDER_KEYS.question_id:
                question_ = munchify({"data": question})
                break
        question = self.client.get_question(self.tender, question_id=TEST_TENDER_KEYS.question_id)
        self.assertEqual(question, question_)

    def test_get_lot(self):
        setup_routing(self.app, routes=["tender_subpage_item"])
        lots = tender_partition(TEST_TENDER_KEYS.tender_id, part="lots")
        for lot in lots:
            if lot['id'] == TEST_TENDER_KEYS.lot_id:
                lot_ = munchify({"data": lot})
                break
        lot = self.client.get_lot(self.tender, lot_id=TEST_TENDER_KEYS.lot_id)
        self.assertEqual(lot, lot_)

    def test_get_bid(self):
        setup_routing(self.app, routes=["tender_subpage_item"])
        bids = tender_partition(TEST_TENDER_KEYS.tender_id, part="bids")
        for bid in bids:
            if bid['id'] == TEST_TENDER_KEYS.bid_id:
                bid_ = munchify({"data": bid})
                break
        bid = self.client.get_bid(self.tender, bid_id=TEST_TENDER_KEYS.bid_id, access_token=API_KEY)
        self.assertEqual(bid , bid_)

    def test_get_location_error(self):
        setup_routing(self.app, routes=["tender_subpage_item"])
        self.assertEqual(self.client.get_question(self.empty_tender, question_id=TEST_TENDER_KEYS.question_id),
                         munchify(loads(location_error('questions'))))
        self.assertEqual(self.client.get_lot(self.empty_tender, lot_id=TEST_TENDER_KEYS.lot_id),
                         munchify(loads(location_error('lots'))))
        self.assertEqual(self.client.get_bid(self.empty_tender, bid_id=TEST_TENDER_KEYS.bid_id, access_token=API_KEY),
                         munchify(loads(location_error('bids'))))


    ###########################################################################
    #             PATCH ITEM TEST
    ###########################################################################

    def test_patch_tender(self):
        setup_routing(self.app, routes=["tender_patch"])
        self.tender.data.description = 'test_patch_tender'
        patched_tender = self.client.patch_tender(self.tender)
        self.assertEqual(patched_tender.data.id, self.tender.data.id)
        self.assertEqual(patched_tender.data.description, self.tender.data.description)

    def test_patch_question(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        question = munchify({"data": {"id": TEST_TENDER_KEYS.question_id, "description": "test_patch_question"}})
        patched_question = self.client.patch_question(self.tender, question)
        self.assertEqual(patched_question.data.id, question.data.id)
        self.assertEqual(patched_question.data.description, question.data.description)

    def test_patch_bid(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        bid = munchify({"data": {"id": TEST_TENDER_KEYS.bid_id, "description": "test_patch_bid"}})
        patched_bid = self.client.patch_bid(self.tender, bid)
        self.assertEqual(patched_bid.data.id, bid.data.id)
        self.assertEqual(patched_bid.data.description, bid.data.description)

    def test_patch_award(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        award = munchify({"data": {"id": TEST_TENDER_KEYS.award_id, "description": "test_patch_award"}})
        patched_award =self.client.patch_award(self.tender, award)
        self.assertEqual(patched_award.data.id, award.data.id)
        self.assertEqual(patched_award.data.description, award.data.description)

    def test_patch_cancellation(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        cancellation = munchify({"data": {"id": TEST_TENDER_KEYS_LIMITED.cancellation_id, "description": "test_patch_cancellation"}})
        patched_cancellation =self.client.patch_cancellation(self.limited_tender, cancellation)
        self.assertEqual(patched_cancellation.data.id, cancellation.data.id)
        self.assertEqual(patched_cancellation.data.description, cancellation.data.description)

    def test_patch_cancellation_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_patch"])
        cancellation_document = munchify({"data": {"id": TEST_TENDER_KEYS_LIMITED.cancellation_document_id, "description": "test_patch_cancellation_document"}})
        patched_cancellation_document =self.client.patch_cancellation_document(self.limited_tender, cancellation_document, TEST_TENDER_KEYS_LIMITED.cancellation_id, TEST_TENDER_KEYS_LIMITED.cancellation_document_id)
        self.assertEqual(patched_cancellation_document.data.id, cancellation_document.data.id)
        self.assertEqual(patched_cancellation_document.data.description, cancellation_document.data.description)

    def test_patch_complaint(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        complaint = munchify({"data": {"id": TEST_TENDER_KEYS_LIMITED.complaint_id, "description": "test_patch_complaint"}})
        patched_complaint =self.client.patch_complaint(self.limited_tender, complaint)
        self.assertEqual(patched_complaint.data.id, complaint.data.id)
        self.assertEqual(patched_complaint.data.description, complaint.data.description)

    def test_patch_qualification(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        qualification = munchify({"data": {"id": TEST_TENDER_KEYS.qualification_id, "description": "test_patch_qualification"}})
        patched_qualification = self.client.patch_qualification(self.tender, qualification)
        self.assertEqual(patched_qualification.data.id, qualification.data.id)
        self.assertEqual(patched_qualification.data.description, qualification.data.description)

    def test_patch_lot(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        lot = munchify({"data": {"id": TEST_TENDER_KEYS.lot_id, "description": "test_patch_lot"}})
        patched_lot = self.client.patch_lot(self.tender, lot)
        self.assertEqual(patched_lot.data.id, lot.data.id)
        self.assertEqual(patched_lot.data.description, lot.data.description)

    def test_patch_document(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        document = munchify({"data": {"id": TEST_TENDER_KEYS.document_id, "title": "test_patch_document.txt"}})
        patched_document = self.client.patch_document(self.tender, document)
        self.assertEqual(patched_document.data.id, document.data.id)
        self.assertEqual(patched_document.data.title, document.data.title)

    def test_patch_contract(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        contract = munchify({"data": {"id": TEST_TENDER_KEYS_LIMITED.contract_id, "title": "test_patch_contract.txt"}})
        patched_contract = self.client.patch_contract(self.limited_tender, contract)
        self.assertEqual(patched_contract.data.id, contract.data.id)
        self.assertEqual(patched_contract.data.title, contract.data.title)

    def test_patch_location_error(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        error = munchify({"data": {"id": TEST_TENDER_KEYS.error_id}, "access": {"token": API_KEY}})
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
        self.assertEqual(self.client.patch_qualification(self.empty_tender, error),
                         munchify(loads(location_error('qualifications'))))

    def test_patch_bid_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_patch"])
        document = munchify({"data": {"id": TEST_TENDER_KEYS.document_id, "title": "test_patch_document.txt"}})
        patched_document = self.client.patch_bid_document(self.tender, document, TEST_TENDER_KEYS.bid_id, TEST_TENDER_KEYS.bid_document_id)
        self.assertEqual(patched_document.data.id, document.data.id)
        self.assertEqual(patched_document.data.title, document.data.title)

    def test_patch_credentials(self):
        setup_routing(self.app, routes=['tender_patch_credentials'])
        patched_credentials = self.client.patch_credentials(self.tender.data.id, self.tender.access['token'])
        self.assertEqual(patched_credentials.data.id, self.tender.data.id)
        self.assertNotEqual(patched_credentials.access.token, self.tender.access['token'])

    ###########################################################################
    #             DOCUMENTS FILE TEST
    ###########################################################################

    def test_get_file(self):
        setup_routing(self.app, routes=["redirect", "download"])
        file_name = 'test_document.txt'
        with open(ROOT + file_name) as local_file:
            test_file_data = local_file.read()
        url = HOST_URL + '/redirect/' + file_name
        doc = self.client.get_file(self.tender, url, API_KEY)
        self.assertEqual(test_file_data, doc[0])
        self.assertEqual(file_name, doc[1])

    def test_get_file_dont_exist_error(self):
        setup_routing(self.app, routes=["redirect", "download"])
        file_name = 'error.txt'
        url = HOST_URL + '/redirect/' + file_name
        self.assertRaises(ResourceNotFound, self.client.get_file,
                          self.tender, url, API_KEY)

    def test_get_file_no_token(self):
        setup_routing(self.app, routes=["redirect", "download"])
        file_name = 'test_document.txt'
        with open(ROOT + file_name) as local_file:
            test_file_data = local_file.read()
        url = HOST_URL + '/redirect/' + file_name
        doc = self.client.get_file(self.tender, url)
        self.assertEqual(test_file_data, doc[0])
        self.assertEqual(file_name, doc[1])

    def test_upload_tender_document(self):
        setup_routing(self.app, routes=["tender_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_document(file_, self.tender)
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_tender_document_path(self):
        setup_routing(self.app, routes=["tender_document_create"])
        file_name = "test_document.txt"
        file_path = ROOT + file_name
        doc = self.client.upload_document(file_path, self.tender)
        self.assertEqual(doc.data.title, file_name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_qualification_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload qualification document text data")
        file_.seek(0)
        doc = self.client.upload_qualification_document(
            file_, self.tender, TEST_TENDER_KEYS.qualification_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_bid_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_bid_financial_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        document_type = "financial_documents"
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id,
            document_type
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_bid_qualification_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        document_type = "qualificationDocuments"
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id,
            document_type
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_bid_eligibility_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        document_type = "eligibility_documents"
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id, document_type
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_cancellation_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_cancellation_document(
            file_, self.limited_tender, TEST_TENDER_KEYS_LIMITED.cancellation_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_complaint_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_complaint_document(
            file_, self.limited_tender, TEST_TENDER_KEYS_LIMITED.complaint_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_award_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        file_ = StringIO()
        file_.name = 'test_award_document.txt'
        file_.write("test upload award document text data")
        file_.seek(0)
        doc = self.client.upload_award_document(
            file_, self.tender, TEST_TENDER_KEYS.award_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_document_type_error(self):
        setup_routing(self.app, routes=["tender_document_create"])
        self.assertRaises(TypeError, self.client.upload_document, (object, self.tender))

    def test_update_bid_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.update_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id,
            TEST_TENDER_KEYS.bid_document_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.bid_document_id)

    def test_update_bid_qualification_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender qualification_document text data")
        file_.seek(0)
        document_type = "qualificationDocuments"
        doc = self.client.update_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id,
            TEST_TENDER_KEYS.bid_qualification_document_id, document_type
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.bid_qualification_document_id)

    def test_update_bid_financial_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender financial_document text data")
        file_.seek(0)
        document_type = "financial_documens"
        doc = self.client.update_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id,
            TEST_TENDER_KEYS.bid_financial_document_id, document_type
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.bid_financial_document_id)

    def test_update_bid_eligibility_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender eligibility_document text data")
        file_.seek(0)
        document_type = "eligibility_documents"
        doc = self.client.update_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id,
            TEST_TENDER_KEYS.bid_eligibility_document_id, document_type
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.bid_eligibility_document_id)

    def test_update_cancellation_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.update_cancellation_document(
            file_, self.limited_tender, TEST_TENDER_KEYS_LIMITED.cancellation_id,
            TEST_TENDER_KEYS_LIMITED.cancellation_document_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS_LIMITED.cancellation_document_id)

    ###########################################################################
    #             DELETE ITEMS LIST TEST
    ###########################################################################

    def test_delete_bid(self):
        setup_routing(self.app, routes=["tender_subpage_item_delete"])
        bid_id = tender_partition(TEST_TENDER_KEYS.tender_id, part="bids")[0]['id']
        deleted_bid = self.client.delete_bid(self.tender, bid_id, API_KEY)
        self.assertFalse(deleted_bid)

    def test_delete_lot(self):
        setup_routing(self.app, routes=["tender_subpage_item_delete"])
        lot_id = tender_partition(TEST_TENDER_KEYS.tender_id, part="lots")[0]['id']
        deleted_lot = self.client.delete_lot(self.tender, lot_id)
        self.assertFalse(deleted_lot)

    def test_delete_location_error(self):
        setup_routing(self.app, routes=["tender_subpage_item_delete"])
        self.assertEqual(self.client.delete_bid(self.empty_tender, TEST_TENDER_KEYS.error_id, API_KEY),
                         munchify(loads(location_error('bids'))))
        self.assertEqual(self.client.delete_lot(self.empty_tender, TEST_TENDER_KEYS.error_id),
                         munchify(loads(location_error('lots'))))


class ContractingUserTestCase(BaseTestClass):
    """"""
    def setUp(self):
        #self._testMethodName
        self.setting_up(client=ContractingClient)

        with open(ROOT + 'contract_' + TEST_CONTRACT_KEYS.contract_id + '.json') as contract:
            self.contract = munchify(load(contract))
            self.contract.update({'access':{"token": API_KEY}})

    def tearDown(self):
        self.server.stop()

    ###########################################################################
    #             CREATE ITEM TEST
    ###########################################################################

    def test_create_contract(self):
        setup_routing(self.app, routes=["contract_create"])
        contract = munchify({'data': 'contract'})
        self.client.create_contract(contract)

    ###########################################################################
    #             DOCUMENTS FILE TEST
    ###########################################################################

    def test_upload_contract_document(self):
        setup_routing(self.app, routes=['contract_document_create'])
        file_ = generate_file_obj('test_document.txt',
                                  'test upload contract document text data')
        doc = self.client.upload_document(file_, self.contract)
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_CONTRACT_KEYS.new_document_id)


if __name__ == '__main__':
    unittest.main()
