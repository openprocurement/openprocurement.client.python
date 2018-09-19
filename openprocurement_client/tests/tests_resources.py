from __future__ import print_function
from gevent import monkey
monkey.patch_all()

from gevent.pywsgi import WSGIServer
from bottle import Bottle
from StringIO import StringIO
from collections import Iterable
from simplejson import loads, load
from munch import munchify
import mock
import sys
import unittest
from openprocurement_client.constants import (
    ELIGIBILITY_DOCUMENTS,
    FINANCIAL_DOCUMENTS,
    QUALIFICATION_DOCUMENTS,
)
from openprocurement_client.exceptions import InvalidResponse, ResourceNotFound
from openprocurement_client.resources.contracts import ContractingClient
from openprocurement_client.resources.plans import PlansClient
from openprocurement_client.resources.tenders import (
    TendersClient, TendersClientSync
)
from openprocurement_client.tests.data_dict import (
    TEST_CONTRACT_KEYS,
    TEST_PLAN_KEYS,
    TEST_TENDER_KEYS,
    TEST_TENDER_KEYS_LIMITED,
)
from openprocurement_client.tests._server import (
    API_KEY,
    API_VERSION,
    AUTH_DS_FAKE,
    DS_HOST_URL,
    DS_PORT,
    HOST_URL,
    PORT,
    ROOT,
    location_error,
    resource_filter,
    resource_partition,
    setup_routing,
    setup_routing_ds,
)


def generate_file_obj(file_name, content):
    file_ = StringIO()
    file_.name = file_name
    file_.write(content)
    file_.seek(0)
    return file_


class BaseTestClass(unittest.TestCase):

    def setting_up(self, client):
        self.app = Bottle()
        self.app.router.add_filter('resource_filter', resource_filter)
        setup_routing(self.app)
        self.server = WSGIServer(('localhost', PORT), self.app, log=None)
        try:
            self.server.start()
        except Exception as error:
            print(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2],
                  file=sys.stderr)
            raise error
        ds_config = {
            'host_url': DS_HOST_URL,
            'auth_ds': AUTH_DS_FAKE
        }
        self.client = client('', host_url=HOST_URL, api_version=API_VERSION,
                             ds_config=ds_config)

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
        with open(ROOT + 'tender_' + TEST_TENDER_KEYS.tender_id + '.json') as\
                tender:
            self.tender = munchify(load(tender))

    def tearDown(self):
        self.server.stop()

    def test_get_tenders(self):
        setup_routing(self.app, routes=["tenders"])
        tenders = self.client.get_tenders()
        self.assertIsInstance(tenders, Iterable)
        self.assertEqual(tenders, self.tenders.data)

    def test_get_latest_tenders(self):
        setup_routing(self.app, routes=["tenders"])
        tenders = self.client.get_latest_tenders(
            '2015-11-16T12:00:00.960077+02:00')
        self.assertIsInstance(tenders, Iterable)
        self.assertEqual(tenders.data, self.tenders.data)

    @mock.patch('openprocurement_client.resources.tenders.TendersClient.'
                'request')
    def test_get_tenders_failed(self, mock_request):
        mock_request.return_value = munchify({'status_code': 404})
        self.client.params['offset'] = 'offset_value'
        with self.assertRaises(KeyError) as e:
            self.client.get_tenders()
        self.assertEqual(e.exception.message, 'offset')

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

    def test_get_latest_plans(self):
        setup_routing(self.app, routes=["plans"])
        plans = self.client.get_latest_plans(
            '2015-11-16T12:00:00.960077+02:00')
        self.assertIsInstance(plans, Iterable)
        self.assertEqual(plans.data, self.plans.data)

    @mock.patch('openprocurement_client.resources.plans.PlansClient.request')
    def test_get_plans_failed(self, mock_request):
        mock_request.return_value = munchify({'status_code': 412})
        self.client.params['offset'] = 'offset_value'
        with self.assertRaises(InvalidResponse) as e:
            self.client.get_plans()
        self.assertEqual(e.exception.message, 'Not described error yet.')

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

    def test_patch_plan(self):
        setup_routing(self.app, routes=['plan_patch'])
        patch_data = {'data': {'description': 'test_patch_plan'}}
        patched_tender = self.client.patch_plan(self.plan.data.id, patch_data)
        self.assertEqual(patched_tender.data.id, self.plan.data.id)
        self.assertEqual(patched_tender.data.description,
                         patch_data['data']['description'])

    def test_create_plan(self):
        setup_routing(self.app, routes=["plan_create"])
        plan = munchify({'data': 'plan'})
        self.assertEqual(self.client.create_plan(plan), plan)


class TendersClientSyncTestCase(BaseTestClass):
    """"""
    def setUp(self):
        self.setting_up(client=TendersClientSync)

        with open(ROOT + 'tenders.json') as tenders:
            self.tenders = munchify(load(tenders))
        with open(ROOT + 'tender_' + TEST_TENDER_KEYS.tender_id + '.json') as \
                tender:
            self.tender = munchify(load(tender))

    def tearDown(self):
        self.server.stop()

    def test_sync_tenders(self):
        setup_routing(self.app, routes=['tenders'])
        tenders = self.client.sync_tenders()
        self.assertIsInstance(tenders.data, Iterable)
        self.assertEqual(tenders.data, self.tenders.data)


class UserTestCase(BaseTestClass):
    """"""
    def setUp(self):
        self.setting_up(client=TendersClient)

        with open(ROOT + 'tender_' + TEST_TENDER_KEYS.tender_id + '.json') \
                as tender:
            self.tender = munchify(load(tender))
            self.tender.update(
                {'access': {'token': TEST_TENDER_KEYS['token']}}
            )
        with open(ROOT + 'tender_' + TEST_TENDER_KEYS.empty_tender + '.json') \
                as tender:
            self.empty_tender = munchify(load(tender))
        with open(
            ROOT + 'tender_' + TEST_TENDER_KEYS_LIMITED.tender_id + '.json') \
                as tender:
            self.limited_tender = munchify(load(tender))

    def tearDown(self):
        self.server.stop()

    ###########################################################################
    #             GET ITEMS LIST TEST
    ###########################################################################

    def test_get_questions(self):
        setup_routing(self.app, routes=["tender_subpage"])
        questions = munchify(
            {'data': self.tender['data'].get('questions', [])}
        )
        self.assertEqual(self.client.get_questions(self.tender.data.id),
                         questions)

    def test_get_documents(self):
        setup_routing(self.app, routes=["tender_subpage"])
        documents = munchify(
            {'data': self.tender['data'].get('documents', [])}
        )
        self.assertEqual(self.client.get_documents(self.tender.data.id),
                         documents)

    def test_get_awards_documents(self):
        setup_routing(self.app, routes=["tender_award_documents"])
        documents = munchify({
            'data': self.tender['data']['awards'][0].get('documents', [])
        })
        self.assertEqual(
            self.client.get_awards_documents(
                self.tender.data.id, self.tender['data']['awards'][0]['id']
            ),
            documents
        )

    def test_get_qualification_documents(self):
        setup_routing(self.app, routes=["tender_qualification_documents"])
        documents = munchify({
            'data':
                self.tender['data']['qualifications'][0].get('documents', [])
        })
        self.assertEqual(
            self.client.get_qualification_documents(
                self.tender.data.id,
                self.tender['data']['qualifications'][0]['id']
            ),
            documents
        )

    def test_get_awards(self):
        setup_routing(self.app, routes=["tender_subpage"])
        awards = munchify({'data': self.tender['data'].get('awards', [])})
        self.assertEqual(self.client.get_awards(self.tender.data.id), awards)

    def test_get_lots(self):
        setup_routing(self.app, routes=["tender_subpage"])
        lots = munchify({'data': self.tender['data'].get('lots', [])})
        self.assertEqual(self.client.get_lots(self.tender.data.id), lots)

    ###########################################################################
    #             CREATE ITEM TEST
    ###########################################################################

    def test_create_tender(self):
        setup_routing(self.app, routes=["tender_create"])
        tender = self.client.create_tender(self.tender)
        assert tender  # check that it is not None

    def test_create_question(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        question = munchify({'data': 'question'})
        self.assertEqual(
            self.client.create_question(self.tender.data.id, question),
            question
        )

    def test_create_bid(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        bid = munchify({'data': 'bid'})
        self.assertEqual(self.client.create_bid(self.tender.data.id, bid),
                         bid)

    def test_create_lot(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        lot = munchify({'data': 'lot'})
        self.assertEqual(self.client.create_lot(self.tender.data.id, lot),
                         lot)

    def test_create_award(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        award = munchify({'data': 'award'})
        self.assertEqual(
            self.client.create_award(self.limited_tender.data.id, award),
            award)

    def test_create_cancellation(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        cancellation = munchify({'data': 'cancellation'})
        self.assertEqual(
            self.client.create_cancellation(
                self.limited_tender.data.id, cancellation
            ),
            cancellation)

    def test_create_complaint(self):
        setup_routing(self.app, routes=["tender_subpage_item_create"])
        complaint = munchify({'data': 'complaint'})
        self.assertEqual(
            self.client.create_complaint(
                self.limited_tender.data.id, complaint
            ),
            complaint
        )

    ###########################################################################
    #             GET ITEM TEST
    ###########################################################################

    def test_get_question(self):
        setup_routing(self.app, routes=["tender_subpage_item"])
        questions = resource_partition(TEST_TENDER_KEYS.tender_id,
                                       part="questions")
        for question in questions:
            if question['id'] == TEST_TENDER_KEYS.question_id:
                question_ = munchify({"data": question})
                break
        question = self.client.get_question(
            self.tender.data.id, question_id=TEST_TENDER_KEYS.question_id
        )
        self.assertEqual(question, question_)

    def test_get_lot(self):
        setup_routing(self.app, routes=["tender_subpage_item"])
        lots = resource_partition(TEST_TENDER_KEYS.tender_id, part="lots")
        for lot in lots:
            if lot['id'] == TEST_TENDER_KEYS.lot_id:
                lot_ = munchify({"data": lot})
                break
        lot = self.client.get_lot(self.tender.data.id,
                                  lot_id=TEST_TENDER_KEYS.lot_id)
        self.assertEqual(lot, lot_)

    def test_get_bid(self):
        setup_routing(self.app, routes=["tender_subpage_item"])
        bids = resource_partition(TEST_TENDER_KEYS.tender_id, part="bids")
        for bid in bids:
            if bid['id'] == TEST_TENDER_KEYS.bid_id:
                bid_ = munchify({"data": bid})
                break
        bid = self.client.get_bid(self.tender.data.id,
                                  bid_id=TEST_TENDER_KEYS.bid_id,
                                  access_token=API_KEY)
        self.assertEqual(bid, bid_)

    def test_get_location_error(self):
        setup_routing(self.app, routes=["tender_subpage_item"])
        self.assertEqual(
            self.client.get_question(
                self.empty_tender.data.id, TEST_TENDER_KEYS.question_id
            ),
            munchify(loads(location_error('questions')))
        )
        self.assertEqual(
            self.client.get_lot(
                self.empty_tender.data.id, lot_id=TEST_TENDER_KEYS.lot_id
            ),
            munchify(loads(location_error('lots')))
        )
        self.assertEqual(
            self.client.get_bid(
                self.empty_tender.data.id, TEST_TENDER_KEYS.bid_id, API_KEY
            ),
            munchify(loads(location_error('bids')))
        )

    ###########################################################################
    #             PATCH ITEM TEST
    ###########################################################################

    def test_patch_tender(self):
        setup_routing(self.app, routes=["tender_patch"])
        patch_data = {'data': {'description': 'test_patch_tender'}}
        patched_tender = self.client.patch_tender(
            self.tender.data.id, patch_data
        )
        self.assertEqual(patched_tender.data.id, self.tender.data.id)
        self.assertEqual(patched_tender.data.description,
                         patch_data['data']['description'])

    def test_patch_question(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        question = munchify({
            "data": {
                "id": TEST_TENDER_KEYS.question_id,
                "description": "test_patch_question"
            }
        })
        patched_question = self.client.patch_question(
            self.tender.data.id, question, question.data.id
        )
        self.assertEqual(patched_question.data.id, question.data.id)
        self.assertEqual(patched_question.data.description,
                         question.data.description)

    def test_patch_bid(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        bid = munchify({
            "data": {
                "id": TEST_TENDER_KEYS.bid_id,
                "description": "test_patch_bid"
            }
        })
        patched_bid = self.client.patch_bid(
            self.tender.data.id, bid, bid.data.id
        )
        self.assertEqual(patched_bid.data.id, bid.data.id)
        self.assertEqual(patched_bid.data.description, bid.data.description)

    def test_patch_award(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        award = munchify({
            "data": {
                "id": TEST_TENDER_KEYS.award_id,
                "description": "test_patch_award"
            }
        })
        patched_award = self.client.patch_award(self.tender.data.id, award,
                                                award.data.id)
        self.assertEqual(patched_award.data.id, award.data.id)
        self.assertEqual(patched_award.data.description,
                         award.data.description)

    def test_patch_cancellation(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        cancellation = munchify({
            "data": {
                "id": TEST_TENDER_KEYS_LIMITED.cancellation_id,
                "description": "test_patch_cancellation"
            }
        })
        patched_cancellation = self.client.patch_cancellation(
            self.limited_tender.data.id, cancellation, cancellation.data.id
        )
        self.assertEqual(patched_cancellation.data.id, cancellation.data.id)
        self.assertEqual(patched_cancellation.data.description,
                         cancellation.data.description)

    def test_patch_cancellation_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_patch"])
        cancellation_document = munchify({
            "data": {
                "id": TEST_TENDER_KEYS_LIMITED.cancellation_document_id,
                "description": "test_patch_cancellation_document"
            }
        })
        patched_cancellation_document = \
            self.client.patch_cancellation_document(
                self.limited_tender.data.id, cancellation_document,
                TEST_TENDER_KEYS_LIMITED.cancellation_id,
                TEST_TENDER_KEYS_LIMITED.cancellation_document_id
            )
        self.assertEqual(patched_cancellation_document.data.id,
                         cancellation_document.data.id)
        self.assertEqual(patched_cancellation_document.data.description,
                         cancellation_document.data.description)

    def test_patch_complaint(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        complaint = munchify({
            "data": {
                "id": TEST_TENDER_KEYS_LIMITED.complaint_id,
                "description": "test_patch_complaint"
            }
        })
        patched_complaint = self.client.patch_complaint(
            self.limited_tender.data.id, complaint, complaint.data.id
        )
        self.assertEqual(patched_complaint.data.id, complaint.data.id)
        self.assertEqual(patched_complaint.data.description,
                         complaint.data.description)

    def test_patch_qualification(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        qualification = munchify({
            "data": {
                "id": TEST_TENDER_KEYS.qualification_id,
                "description": "test_patch_qualification"
            }
        })
        patched_qualification = self.client.patch_qualification(
            self.tender.data.id, qualification, qualification.data.id
        )
        self.assertEqual(patched_qualification.data.id, qualification.data.id)
        self.assertEqual(patched_qualification.data.description,
                         qualification.data.description)

    def test_patch_lot(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        lot = munchify({
            "data": {
                "id": TEST_TENDER_KEYS.lot_id,
                "description": "test_patch_lot"
            }
        })
        patched_lot = self.client.patch_lot(
            self.tender.data.id, lot, lot.data.id
        )
        self.assertEqual(patched_lot.data.id, lot.data.id)
        self.assertEqual(patched_lot.data.description, lot.data.description)

    def test_patch_document(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        document = munchify({
            "data": {
                "id": TEST_TENDER_KEYS.document_id,
                "title": "test_patch_document.txt"
            }
        })
        patched_document = self.client.patch_document(
            self.tender.data.id, document, document.data.id
        )
        self.assertEqual(patched_document.data.id, document.data.id)
        self.assertEqual(patched_document.data.title, document.data.title)

    def test_patch_contract(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        contract = munchify({
            "data": {
                "id": TEST_TENDER_KEYS_LIMITED.contract_id,
                "title": "test_patch_contract.txt"
            }
        })
        patched_contract = self.client.patch_contract(
            self.limited_tender.data.id, contract, contract.data.id
        )
        self.assertEqual(patched_contract.data.id, contract.data.id)
        self.assertEqual(patched_contract.data.title, contract.data.title)

    def test_patch_location_error(self):
        setup_routing(self.app, routes=["tender_subpage_item_patch"])
        error = munchify({
            "data": {"id": TEST_TENDER_KEYS.error_id},
            "access": {"token": API_KEY}
        })
        self.assertEqual(
            self.client.patch_question(
                self.empty_tender.data.id, error, error.data.id
            ),
            munchify(loads(location_error('questions')))
        )
        self.assertEqual(
            self.client.patch_bid(
                self.empty_tender.data.id, error, error.data.id
            ),
            munchify(loads(location_error('bids')))
        )
        self.assertEqual(
            self.client.patch_award(
                self.empty_tender.data.id, error, error.data.id
            ),
            munchify(loads(location_error('awards')))
        )
        self.assertEqual(
            self.client.patch_lot(
                self.empty_tender.data.id, error, error.data.id
            ),
            munchify(loads(location_error('lots')))
        )
        self.assertEqual(
            self.client.patch_document(
                self.empty_tender.data.id, error, error.data.id
            ),
            munchify(loads(location_error('documents')))
        )
        self.assertEqual(
            self.client.patch_qualification(
                self.empty_tender.data.id, error, error.data.id
            ),
            munchify(loads(location_error('qualifications')))
        )

    def test_patch_bid_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_patch"])
        document = munchify({
            "data": {
                "id": TEST_TENDER_KEYS.document_id,
                "title": "test_patch_document.txt"
            }
        })
        patched_document = self.client.patch_bid_document(
            self.tender.data.id, document, TEST_TENDER_KEYS.bid_id,
            TEST_TENDER_KEYS.bid_document_id
        )
        self.assertEqual(patched_document.data.id, document.data.id)
        self.assertEqual(patched_document.data.title, document.data.title)

    def test_patch_credentials(self):
        setup_routing(self.app, routes=['tender_patch_credentials'])
        patched_credentials = self.client.patch_credentials(
            self.tender.data.id, self.tender.access['token']
        )
        self.assertEqual(patched_credentials.data.id, self.tender.data.id)
        self.assertNotEqual(patched_credentials.access.token,
                            self.tender.access['token'])
        self.assertEqual(patched_credentials.access.token,
                         TEST_TENDER_KEYS['new_token'])

    ###########################################################################
    #             DOCUMENTS FILE TEST
    ###########################################################################

    def test_get_file(self):
        setup_routing(self.app, routes=["redirect", "download"])
        file_name = 'test_document.txt'
        with open(ROOT + file_name) as local_file:
            test_file_data = local_file.read()
        url = HOST_URL + '/redirect/' + file_name
        doc = self.client.get_file(url, API_KEY)
        self.assertEqual(test_file_data, doc[0])
        self.assertEqual(file_name, doc[1])

    def test_get_file_dont_exist_error(self):
        setup_routing(self.app, routes=["redirect", "download"])
        file_name = 'error.txt'
        url = HOST_URL + '/redirect/' + file_name
        self.assertRaises(ResourceNotFound, self.client.get_file, url, API_KEY)

    def test_get_file_no_token(self):
        setup_routing(self.app, routes=["redirect", "download"])
        file_name = 'test_document.txt'
        with open(ROOT + file_name) as local_file:
            test_file_data = local_file.read()
        url = HOST_URL + '/redirect/' + file_name
        doc = self.client.get_file(url)
        self.assertEqual(test_file_data, doc[0])
        self.assertEqual(file_name, doc[1])

    def test_upload_tender_document(self):
        setup_routing(self.app, routes=["tender_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_document(
            file_, self.tender,
            doc_type='tenderNotice'
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_tender_document_path(self):
        setup_routing(self.app, routes=["tender_document_create"])
        file_name = "test_document.txt"
        file_path = ROOT + file_name
        doc = self.client.upload_document(
            file_path, self.tender.data.id,
            access_token=self.tender.access['token']
        )
        self.assertEqual(doc.data.title, file_name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    @mock.patch('openprocurement_client.resources.document_service.'
                'DocumentServiceClient.request')
    def test_upload_tender_document_path_failed(self, mock_request):
        mock_request.return_value = munchify({'status_code': 204})
        setup_routing(self.app, routes=["tender_document_create"])
        file_name = "test_document.txt"
        file_path = ROOT + file_name
        with self.assertRaises(InvalidResponse):
            self.client.upload_document(
                file_path, self.tender.data.id,
                access_token=self.tender.access['token']
            )

    def test_upload_qualification_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload qualification document text data")
        file_.seek(0)
        doc = self.client.upload_qualification_document(
            file_, self.tender.data.id, TEST_TENDER_KEYS.qualification_id
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
            file_, self.tender.data.id, TEST_TENDER_KEYS.bid_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_bid_financial_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        document_type = FINANCIAL_DOCUMENTS
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_bid_document(
            file_, self.tender.data.id, TEST_TENDER_KEYS.bid_id,
            doc_type=document_type
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_bid_qualification_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        document_type = QUALIFICATION_DOCUMENTS
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_bid_document(
            file_, self.tender.data.id, TEST_TENDER_KEYS.bid_id,
            doc_type=document_type
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_bid_eligibility_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_create"])
        document_type = ELIGIBILITY_DOCUMENTS
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.upload_bid_document(
            file_, self.tender.data.id, TEST_TENDER_KEYS.bid_id,
            doc_type=document_type
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
            file_, self.limited_tender.data.id,
            TEST_TENDER_KEYS_LIMITED.cancellation_id
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
            file_, self.limited_tender.data.id,
            TEST_TENDER_KEYS_LIMITED.complaint_id
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
            file_, self.tender.data.id, TEST_TENDER_KEYS.award_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_TENDER_KEYS.new_document_id)

    def test_upload_document_type_error(self):
        setup_routing(self.app, routes=["tender_document_create"])
        self.assertRaises(
            TypeError, self.client.upload_document, (object, self.tender)
        )

    def test_update_bid_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.update_bid_document(
            file_, self.tender.data.id, TEST_TENDER_KEYS.bid_id,
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
        subitem_name = QUALIFICATION_DOCUMENTS
        doc = self.client.update_bid_document(
            file_, self.tender.data.id, TEST_TENDER_KEYS.bid_id,
            TEST_TENDER_KEYS.bid_qualification_document_id,
            subitem_name=subitem_name
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id,
                         TEST_TENDER_KEYS.bid_qualification_document_id)

    def test_update_bid_financial_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender financial_document text data")
        file_.seek(0)
        subitem_name = FINANCIAL_DOCUMENTS
        doc = self.client.update_bid_document(
            file_, self.tender.data.id, TEST_TENDER_KEYS.bid_id,
            TEST_TENDER_KEYS.bid_financial_document_id,
            subitem_name=subitem_name
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id,
                         TEST_TENDER_KEYS.bid_financial_document_id)

    def test_update_bid_eligibility_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender eligibility_document text data")
        file_.seek(0)
        subitem_name = ELIGIBILITY_DOCUMENTS
        doc = self.client.update_bid_document(
            file_, self.tender, TEST_TENDER_KEYS.bid_id,
            TEST_TENDER_KEYS.bid_eligibility_document_id,
            subitem_name=subitem_name,
            doc_type='eligibilityCriteria'
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id,
                         TEST_TENDER_KEYS.bid_eligibility_document_id)

    def test_update_cancellation_document(self):
        setup_routing(self.app, routes=["tender_subpage_document_update"])
        file_ = StringIO()
        file_.name = 'test_document.txt'
        file_.write("test upload tender document text data")
        file_.seek(0)
        doc = self.client.update_cancellation_document(
            file_, self.limited_tender.data.id,
            TEST_TENDER_KEYS_LIMITED.cancellation_id,
            TEST_TENDER_KEYS_LIMITED.cancellation_document_id
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id,
                         TEST_TENDER_KEYS_LIMITED.cancellation_document_id)

    ###########################################################################
    #             DELETE ITEMS LIST TEST
    ###########################################################################

    def test_delete_bid(self):
        setup_routing(self.app, routes=["tender_subpage_item_delete"])
        bid_id = resource_partition(
            TEST_TENDER_KEYS.tender_id, part="bids")[0]['id']
        deleted_bid = self.client.delete_bid(self.tender.data.id, bid_id,
                                             API_KEY)
        self.assertFalse(deleted_bid)

    def test_delete_lot(self):
        setup_routing(self.app, routes=["tender_subpage_item_delete"])
        lot_id = resource_partition(
            TEST_TENDER_KEYS.tender_id, part="lots")[0]['id']
        deleted_lot = self.client.delete_lot(self.tender.data.id, lot_id)
        self.assertFalse(deleted_lot)

    def test_delete_location_error(self):
        setup_routing(self.app, routes=["tender_subpage_item_delete"])
        self.assertEqual(
            self.client.delete_bid(
                self.empty_tender.data.id, TEST_TENDER_KEYS.error_id, API_KEY
            ),
            munchify(loads(location_error('bids')))
        )
        self.assertEqual(
            self.client.delete_lot(
                self.empty_tender, TEST_TENDER_KEYS.error_id
            ),
            munchify(loads(location_error('lots')))
        )


class ContractingUserTestCase(BaseTestClass):
    """"""
    def setUp(self):
        self.setting_up(client=ContractingClient)

        with open(ROOT + 'contract_' + TEST_CONTRACT_KEYS.contract_id +
                  '.json') as contract:
            self.contract = munchify(load(contract))
            self.contract.update(
                {'access': {'token': TEST_CONTRACT_KEYS.contract_token}}
            )

        with open(ROOT + 'contracts.json') as contracts:
            self.contracts = munchify(load(contracts))

        with open(ROOT + 'change_' + TEST_CONTRACT_KEYS.change_id +
                  '.json') as change:
            self.change = munchify(load(change))

        with open(ROOT + 'contracts.json') as contracts:
            self.contracts = munchify(load(contracts))

        with open(ROOT + 'milestone_' + TEST_CONTRACT_KEYS.milestone_id + '.json') as m:
            self.milestone = munchify(load(m))

    def tearDown(self):
        self.server.stop()

    ###########################################################################
    #             GET ITEM TEST
    ###########################################################################

    def test_get_contract(self):
        setup_routing(self.app, routes=["contract"])
        contract = self.client.get_contract(self.contract.data['id'])
        self.assertEqual(contract, self.contract)

    def test_get_contracts(self):
        setup_routing(self.app, routes=["contracts"])
        contracts = self.client.get_contracts()
        self.assertIsInstance(contracts, Iterable)
        self.assertEqual(contracts, self.contracts.data)

    def test_get_contract_location_error(self):
        setup_routing(self.app, routes=["contract"])
        contract = self.client.get_contract(TEST_CONTRACT_KEYS.error_id)
        self.assertEqual(contract, munchify(loads(location_error('contract'))))

    ###########################################################################
    #             CREATE ITEM TEST
    ###########################################################################

    def test_create_contract(self):
        setup_routing(self.app, routes=['contract_create'])
        contract = self.client.create_contract(self.contract)
        self.assertEqual(contract, self.contract)

    def test_create_change(self):
        setup_routing(self.app, routes=['contract_subpage_item_create'])
        change = self.client.create_change(self.contract.data.id, '', self.change)
        self.assertEqual(change, self.change)

    ###########################################################################
    #             DOCUMENTS FILE TEST
    ###########################################################################

    def test_upload_contract_document(self):
        setup_routing(self.app, routes=['contract_document_create'])
        file_ = generate_file_obj('test_document.txt',
                                  'test upload contract document text data')
        doc = self.client.upload_document(
            file_, self.contract.data.id,
            access_token=self.contract.access['token']
        )
        self.assertEqual(doc.data.title, file_.name)
        self.assertEqual(doc.data.id, TEST_CONTRACT_KEYS.new_document_id)

    ###########################################################################
    #             PATCH ITEM TEST
    ###########################################################################

    def test_patch_document(self):
        setup_routing(self.app, routes=['contract_subpage_item_patch'])
        document = munchify({'data': {'id': TEST_CONTRACT_KEYS.document_id,
                                      'title': 'test_patch_document.txt'}})
        patched_document = self.client.patch_document(
            self.contract.data.id, document, document.data.id,
            self.contract.access['token'])
        self.assertEqual(patched_document.data.id, document.data.id)
        self.assertEqual(patched_document.data.title, document.data.title)

    def test_patch_change(self):
        setup_routing(self.app, routes=['contract_change_patch'])
        patch_change_data = {
            'data': {
                'rationale': TEST_CONTRACT_KEYS['patch_change_rationale']
            }
        }
        patched_change = self.change.copy()
        patched_change['data'].update(patch_change_data['data'])
        patched_change = munchify(patched_change)
        response_change = self.client.patch_change(self.contract.data.id, self.change.data.id, '',
                                                   data=patch_change_data)

        self.assertEqual(response_change, patched_change)

    def test_retrieve_contract_credentials(self):
        setup_routing(self.app, routes=['contract_patch_credentials'])
        patched_credentials = self.client.patch_credentials(
            self.contract.data.id, self.contract.access['token'])
        self.assertEqual(patched_credentials.data.id, self.contract.data.id)
        self.assertNotEqual(patched_credentials.access.token,
                            self.contract.access['token'])
        self.assertEqual(patched_credentials.access.token,
                         TEST_CONTRACT_KEYS['new_token'])

    ###########################################################################

    def test_patch_contract(self):
        setup_routing(self.app, routes=["contract_patch"])
        patch_data = {'data': {'description': 'test_patch_contract'}}
        access_token = self.contract.access['token']
        patched_contract = self.client.patch_contract(self.contract.data.id, access_token, patch_data)
        self.assertEqual(patched_contract.data.id, self.contract.data.id)
        self.assertEqual(patched_contract.data.description, patch_data['data']['description'])


    def test_patch_milestone(self):
        setup_routing(self.app, routes=('contract_patch_milestone',))
        patch_data = {'data': {'description': 'test_patch_contract_milestone'}}
        access_token = self.contract.access['token']
        patched_milestone = self.client.patch_milestone(self.contract.data.id, self.milestone.id, access_token, patch_data)
        self.assertEqual(patched_milestone.data.id, self.milestone.id)
        self.assertEqual(patched_milestone.data.description, patch_data['data']['description'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ViewerTenderTestCase))
    suite.addTest(unittest.makeSuite(ViewerPlanTestCase))
    suite.addTest(unittest.makeSuite(ViewerPlanTestCase))
    suite.addTest(unittest.makeSuite(UserTestCase))
    suite.addTest(unittest.makeSuite(ContractingUserTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
