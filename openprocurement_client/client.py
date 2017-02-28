import logging

from .api_base_client import APIBaseClient, verify_file
from .exceptions import InvalidResponse

from iso8601 import parse_date
from munch import munchify
from retrying import retry
from simplejson import loads


logger = logging.getLogger(__name__)

IGNORE_PARAMS = ('uri', 'path')


class TendersClient(APIBaseClient):
    """client for tenders"""

    def __init__(self,
                 key,
                 resource='tenders',  # another possible value is 'auctions'
                 host_url=None,
                 api_version=None,
                 params=None,
                 ds_client=None,
                 user_agent=None):
        super(TendersClient, self).__init__(
            key, resource, host_url, api_version, params, ds_client,
            user_agent
        )
        self.headers = {'Content-Type': 'application/json'}

    ###########################################################################
    #             GET ITEMS LIST API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_tenders(self, params={}, feed='changes'):
        params['feed'] = feed
        self._update_params(params)
        response = self.request('GET',
                                self.prefix_path,
                                params_dict=self.params)
        if response.status_code == 200:
            tender_list = munchify(loads(response.text))
            self._update_params(tender_list.next_page)
            return tender_list.data
        elif response.status_code == 404:
            del self.params['offset']

        raise InvalidResponse(response)

    def get_latest_tenders(self, date, tender_id):
        iso_dt = parse_date(date)
        dt = iso_dt.strftime('%Y-%m-%d')
        tm = iso_dt.strftime('%H:%M:%S')
        response = self._get_resource_item(
            '{}?offset={}T{}&opt_fields=tender_id&mode=test'.format(
                self.prefix_path,
                dt,
                tm
            )
        )
        if response.status_code == 200:
            tender_list = munchify(loads(response.text))
            self._update_params(tender_list.next_page)
            return tender_list.data
        raise InvalidResponse(response)

    def _get_tender_resource_list(self, tender, items_name):
        return self._get_resource_item(
            '{}/{}/{}'.format(self.prefix_path, tender.data.id, items_name),
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def get_questions(self, tender):
        return self._get_tender_resource_list(tender, 'questions')

    def get_documents(self, tender):
        return self._get_tender_resource_list(tender, 'documents')

    def get_awards(self, tender):
        return self._get_tender_resource_list(tender, 'awards')

    def get_lots(self, tender):
        return self._get_tender_resource_list(tender, 'lots')

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################

    def _create_tender_resource_item(self, tender, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, tender.data.id, items_name),
            item_obj,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def create_tender(self, tender):
        return self._create_resource_item(self.prefix_path, tender)

    def create_question(self, tender, question):
        return self._create_tender_resource_item(tender, question, 'questions')

    def create_bid(self, tender, bid):
        return self._create_tender_resource_item(tender, bid, 'bids')

    def create_lot(self, tender, lot):
        return self._create_tender_resource_item(tender, lot, 'lots')

    def create_award(self, tender, award):
        return self._create_tender_resource_item(tender, award, 'awards')

    def create_cancellation(self, tender, cancellation):
        return self._create_tender_resource_item(
            tender, cancellation, 'cancellations'
        )

    def create_complaint(self, tender, complaint):
        return self\
            ._create_tender_resource_item(tender, complaint, 'complaints')

    def create_award_complaint(self, tender, complaint, award_id):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, tender.data.id,
                              'awards/{0}/complaints'.format(award_id)),
            complaint,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def create_thin_document(self, tender, document_data):
        return self._create_resource_item(
            '{}/{}/documents'.format(
                self.prefix_path,
                tender.data.id
            ),
            document_data,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    def get_tender(self, id):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id))

    def _get_tender_resource_item(self, tender, item_id, items_name,
                                  access_token=''):
        if access_token:
            headers = {'X-Access-Token': access_token}
        else:
            headers = {'X-Access-Token': self._get_access_token(tender)}
        return self._get_resource_item(
            '{}/{}/{}/{}'.format(self.prefix_path,
                                 tender.data.id,
                                 items_name,
                                 item_id),
            headers=headers
        )

    def get_question(self, tender, question_id):
        return self._get_tender_resource_item(tender, question_id, 'questions')

    def get_bid(self, tender, bid_id, access_token):
        return self._get_tender_resource_item(tender, bid_id, 'bids',
                                              access_token)

    def get_lot(self, tender, lot_id):
        return self._get_tender_resource_item(tender, lot_id, 'lots')

    def get_file(self, tender, url, access_token=None):
        headers = {}
        if access_token:
            headers = {'X-Access-Token': access_token}

        headers.update(self.headers)
        response_item = self.request('GET', url, headers=headers)

        # if response_item.status_code == 302:
        #     response_obj = request(response_item.headers['location'])
        if response_item.status_code == 200:
            return response_item.text, \
                response_item.headers['Content-Disposition'] \
                .split("; filename=")[1].strip('"')
        raise InvalidResponse(response_item)

    def extract_credentials(self, id):
        return self._get_resource_item(
            '{}/{}/extract_credentials'.format(self.prefix_path, id)
        )

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################

    def patch_tender(self, tender):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, tender['data']['id']),
            payload=tender,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def patch_question(self, tender, question):
        return self._patch_obj_resource_item(tender, question, 'questions')

    def patch_bid(self, tender, bid):
        return self._patch_obj_resource_item(tender, bid, 'bids')

    def patch_bid_document(self, tender, document_data, bid_id, document_id):
        return self._patch_resource_item(
            '{}/{}/{}/{}/documents/{}'.format(
                self.prefix_path, tender.data.id, 'bids', bid_id, document_id
            ),
            payload=document_data,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def patch_award(self, tender, award):
        return self._patch_obj_resource_item(tender, award, 'awards')

    def patch_cancellation(self, tender, cancellation):
        return self._patch_obj_resource_item(
            tender, cancellation, 'cancellations'
        )

    def patch_cancellation_document(
            self, tender, cancellation, cancellation_id, cancellation_doc_id
    ):
        return self._patch_resource_item(
            '{}/{}/{}/{}/documents/{}'.format(
                self.prefix_path, tender.data.id, 'cancellations',
                cancellation_id, cancellation_doc_id
            ),
            payload=cancellation,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def patch_complaint(self, tender, complaint):
        return self._patch_obj_resource_item(
            tender, complaint, 'complaints'
        )

    def patch_award_complaint(self, tender, complaint, award_id):
        return self._patch_resource_item(
            '{}/{}/awards/{}/complaints/{}'.format(
                self.prefix_path, tender.data.id, award_id, complaint.data.id
            ),
            payload=complaint,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def patch_lot(self, tender, lot):
        return self._patch_obj_resource_item(tender, lot, 'lots')

    def patch_qualification(self, tender, qualification):
        return self._patch_obj_resource_item(
            tender, qualification, 'qualifications'
        )

    def patch_contract(self, tender, contract):
        return self._patch_obj_resource_item(tender, contract, 'contracts')

    def patch_contract_document(self, tender, document_data,
                                contract_id, document_id):
        return self._patch_resource_item(
            '{}/{}/{}/{}/documents/{}'.format(
                self.prefix_path, tender.data.id, 'contracts',
                contract_id, document_id
            ),
            payload=document_data,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def patch_credentials(self, id, access_token):
        return self._patch_resource_item(
            '{}/{}/credentials'.format(self.prefix_path, id),
            payload={},
            headers={'X-Access-Token': access_token}
        )

    ###########################################################################
    #             UPLOAD FILE API METHODS
    ###########################################################################

    @verify_file
    def upload_bid_document(self, file_, tender, bid_id, doc_type='documents',
                            use_ds_client=True, doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/bids/{}/{}'.format(
                self.prefix_path,
                tender.data.id,
                bid_id,
                doc_type
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def update_bid_document(self, file_, tender, bid_id, document_id,
                            doc_type='documents', use_ds_client=True,
                            doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/bids/{}/{}/{}'.format(
                self.prefix_path,
                tender.data.id,
                bid_id,
                doc_type,
                document_id
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            method='put',
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def upload_cancellation_document(self, file_, tender, cancellation_id,
                                     use_ds_client=True,
                                     doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/cancellations/{}/documents'.format(
                self.prefix_path,
                tender.data.id,
                cancellation_id,
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def update_cancellation_document(self, file_, tender, cancellation_id,
                                     document_id, use_ds_client=True,
                                     doc_registration=True):
            return self._upload_resource_file(
                '{}/{}/cancellations/{}/documents/{}'.format(
                    self.prefix_path,
                    tender.data.id,
                    cancellation_id,
                    document_id
                ),
                file_=file_,
                headers={'X-Access-Token': self._get_access_token(tender)},
                method='put',
                use_ds_client=use_ds_client,
                doc_registration=doc_registration
            )

    @verify_file
    def upload_complaint_document(self, file_, tender, complaint_id,
                                  use_ds_client=True, doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/complaints/{}/documents'.format(
                self.prefix_path,
                tender.data.id,
                complaint_id),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def upload_award_complaint_document(self, file_, tender, award_id,
                                        complaint_id, use_ds_client=True,
                                        doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/awards/{}/complaints/{}/documents'.format(
                self.prefix_path,
                tender.data.id,
                award_id,
                complaint_id),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def upload_qualification_document(self, file_, tender, qualification_id,
                                      use_ds_client=True,
                                      doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/qualifications/{}/documents'.format(
                self.prefix_path,
                tender.data.id,
                qualification_id
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def upload_award_document(self, file_, tender, award_id,
                              use_ds_client=True, doc_registration=True):
        return self._upload_resource_file(
            '{}/{}/awards/{}/documents'.format(
                self.prefix_path,
                tender.data.id,
                award_id
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def upload_contract_document(self, file_, tender, contract_id,
                                 doc_type='documents', use_ds_client=True,
                                 doc_registration=True):
        # TODO: find out what actually depends on the doc_type parameter.
        # TODO: is it necessary to pass it here?
        return self._upload_resource_file(
            '{}/{}/contracts/{}/documents'.format(
                self.prefix_path,
                tender.data.id,
                contract_id
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    ###########################################################################
    #             DELETE ITEMS LIST API METHODS
    ###########################################################################

    def delete_bid(self, tender, bid, access_token=None):
        logger.info('delete_lot is deprecated. In next update this function '
                    'will takes bid_id and access_token instead bid.')
        if isinstance(bid, basestring):
            bid_id = bid
            access_token = access_token
        else:
            bid_id = bid.data.id
            access_token = getattr(getattr(bid, 'access', ''), 'token', '')
        return self._delete_resource_item(
            '{}/{}/bids/{}'.format(
                self.prefix_path,
                tender.data.id,
                bid_id
            ),
            headers={'X-Access-Token': access_token}
        )

    def delete_lot(self, tender, lot):
        logger.info('delete_lot is deprecated. In next update this function '
                    'will takes lot_id instead lot.')
        if isinstance(lot, basestring):
            lot_id = lot
        else:
            lot_id = lot.data.id
        return self._delete_resource_item(
            '{}/{}/lots/{}'.format(
                self.prefix_path,
                tender.data.id,
                lot_id
            ),
            headers={'X-Access-Token': self._get_access_token(tender)}
        )
    ###########################################################################


class Client(TendersClient):
    """client for tenders for backward compatibility"""


class TendersClientSync(TendersClient):

    def sync_tenders(self, params={}, extra_headers={}):
        params['feed'] = 'changes'
        self.headers.update(extra_headers)
        response = self.request('GET', self.prefix_path, params_dict=params)
        if response.status_code == 200:
            tender_list = munchify(loads(response.text))
            return tender_list

    @retry(stop_max_attempt_number=5)
    def get_tender(self, id, extra_headers={}):
        self.headers.update(extra_headers)
        return super(TendersClientSync, self).get_tender(id)
