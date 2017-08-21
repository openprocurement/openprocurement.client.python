import logging

from .api_base_client import APIBaseClient, APITemplateClient, verify_file
from .exceptions import InvalidResponse, IdNotFound

from iso8601 import parse_date
from munch import munchify
from retrying import retry
from simplejson import loads


logger = logging.getLogger(__name__)

IGNORE_PARAMS = ('uri', 'path')


class APIClient(APIBaseClient):
    """ API Client """

    def __init__(self, *args, **kwargs):
        super(APIClient, self).__init__(*args, **kwargs)

    ###########################################################################
    #                        CREATE CLIENT METHODS
    ###########################################################################

    def create_resource_item(self, resource_item):
        return self._create_resource_item(self.prefix_path, resource_item)

    def create_resource_item_subitem(self, resource_item, subitem_obj,
                                     subitem_name, resource_item_id=None,
                                     depth_path=None, access_token=None):
        resource_item_id = resource_item_id or resource_item['data'].get('id')
        access_token = access_token or self._get_access_token(resource_item)
        headers = {'X-Access-Token': access_token}
        if depth_path:
            url = '{}/{}/{}/{}'.format(self.prefix_path, resource_item_id,
                                       depth_path, subitem_name)
        else:
            url = '{}/{}/{}'.format(self.prefix_path, resource_item_id,
                                    subitem_name)
        return self._create_resource_item(url, subitem_obj, headers=headers)

    ###########################################################################
    #                          GET CLIENT METHODS
    ###########################################################################

    def get_resource_item(self, resource_item_id, headers=None):
        return self._get_resource_item('{}/{}'.format(
            self.prefix_path, resource_item_id), headers=headers)

    def get_resource_item_submitem(self, resource_item, subitem_id_or_name,
                                   resource_item_id=None, access_token=None,
                                   depth_path=None):
        resource_item_id = resource_item_id or resource_item['data'].get('id')
        access_token = access_token or self._get_access_token(resource_item)
        headers = {'X-Access-Token': access_token}
        if depth_path:
            url = '{}/{}/{}/{}'.format(self.prefix_path, resource_item_id,
                                       depth_path, subitem_id_or_name)
        else:
            url = '{}/{}/{}'.format(self.prefix_path, resource_item_id,
                                    subitem_id_or_name)
        return self._get_resource_item(url, headers=headers)

    def get_resource_items(self, params=None, feed='changes'):
        return self._get_resource_items(params=params, feed=feed)

    def get_file(self, url, access_token=None):
        headers = {'X-Access-Token': access_token} if access_token else {}

        headers.update(self.headers)
        response_item = self.request('GET', url, headers=headers)

        # if response_item.status_code == 302:
        #     response_obj = request(response_item.headers['location'])
        if response_item.status_code == 200:
            return response_item.text, \
                response_item.headers['Content-Disposition'] \
                .split("; filename=")[1].strip('"')
        raise InvalidResponse(response_item)

    def get_file_properties(self, url, file_hash, access_token=None):
        headers = {'X-Access-Token': access_token} if access_token else {}
        headers.update(self.headers)
        response_item = self.request('GET', url, headers=headers)
        if response_item.status_code == 200:
            file_properties = {
                'Content_Disposition':
                    response_item.headers['Content-Disposition'],
                'Content_Type': response_item.headers['Content-Type'],
                'url': url,
                'hash': file_hash
            }
            return file_properties
        raise InvalidResponse(response_item)

    ###########################################################################
    #                          PATCH CLIENT METHODS
    ###########################################################################

    def patch_credentials(self, resource_item_id, access_token):
        return self._patch_resource_item(
            '{}/{}/credentials'.format(self.prefix_path, resource_item_id),
            payload=None,
            headers={'X-Access-Token': access_token}
        )

    def patch_resource_item(self, resource_item, resource_item_id=None):
        resource_item_id = resource_item_id or resource_item['data'].get('id')
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, resource_item_id),
            payload=resource_item,
            headers={'X-Access-Token': self._get_access_token(resource_item)}
        )

    def patch_resource_item_subitem(self, resource_item, subitem_obj,
                                    subitem_name, resource_item_id=None,
                                    subitem_id=None, depth_path=None,
                                    headers=None):
        subitem_id = subitem_id or subitem_obj['data'].get('id')
        resource_item_id = resource_item_id or resource_item['data'].get('id')
        access_token = self._get_access_token(resource_item)
        headers = {'X-Access-Token': access_token}
        if depth_path:
            url = '{}/{}/{}/{}/{}'.format(
                self.prefix_path, resource_item_id, depth_path, subitem_name,
                subitem_id
            )
        else:
            url = '{}/{}/{}/{}'.format(
                self.prefix_path, resource_item_id, subitem_name, subitem_id
            )
        return self._patch_resource_item(url, subitem_obj, headers=headers)

    ###########################################################################
    #                          UPLOAD CLIENT METHODS
    ###########################################################################

    @verify_file
    def upload_document(
            self, file_, resource_item, use_ds_client=True,
            doc_registration=True, resource_item_id=None, depth_path=None):
        resource_item_id = resource_item_id or resource_item['data'].get('id')
        headers = {'X-Access-Token': self._get_access_token(tender)}
        if depth_path:
            url = '{}/{}/{}/documents'.format(
                self.prefix_path, resource_item_id, depth_path
            )
        else:
            url = '{}/{}/documents'.format(self.prefix_path, resource_item_id)
        return self._upload_resource_file(
            url, file_=file_, headers=headers, use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    # def patch_document(self, obj, document):
    #     return self._patch_obj_resource_item(obj, document, 'documents')
    #
    # @verify_file
    # def upload_document(self, file_, obj, use_ds_client=True,
    #                     doc_registration=True):
    #     return self._upload_resource_file(
    #         '{}/{}/documents'.format(
    #             self.prefix_path,
    #             obj.data.id
    #         ),
    #         file_=file_,
    #         headers={'X-Access-Token': self._get_access_token(obj)},
    #         use_ds_client=use_ds_client,
    #         doc_registration=doc_registration
    #     )




    def extract_credentials(self, resource_item_id):
        return self._get_resource_item(
            '{}/{}/extract_credentials'.format(self.prefix_path,
                                               resource_item_id)
        )


class TendersClient(APIClient):
    """client for tenders"""

    def __init__(self, *args, **kwargs):
        super(TendersClient, self).__init__(*args, **kwargs)

    ###########################################################################
    #             GET ITEMS LIST API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_tenders(self, params=None, feed='changes'):
        return self.get_resource_items(params=params, feed=feed)

    def get_latest_tenders(self, date, tender_id):
        iso_dt = parse_date(date)
        dt = iso_dt.strftime('%Y-%m-%d')
        tm = iso_dt.strftime('%H:%M:%S')
        data = self._get_resource_item(
            '{}?offset={}T{}&opt_fields=tender_id&mode=test'.format(
                self.prefix_path,
                dt,
                tm
            )
        )
        return data

    def get_questions(self, tender, tender_id=None):
        return self.get_resource_item_subitem(
            tender, 'questions', resource_item_id=tender_id
        )

    def get_documents(self, tender, tender_id=None):
        return self.get_resource_item_subitem(
            tender, 'documents', resource_item_id=tender_id)

    def get_awards_documents(self, tender, award_id, tender_id=None):
        return self.get_resource_item_subitem(
            tender, 'documents', depth_path='awards/{}'.format(award_id),
            resource_item_id=tender_id
        )

    def get_qualification_documents(self, tender, qualification_id,
                                    tender_id=None):
        return self.get_resource_item_subitem(
            tender, 'documents',
            depth_path='qualifications/{}'.format(qualification_id),
            resource_item_id=tender_id
        )

    def get_awards(self, tender, tender_id=None):
        return self.get_resource_item_subitem(
            tender, 'awards', resource_item_id=tender_id
        )

    def get_lots(self, tender, tender_id=None):
        return self.get_resource_item_subitem(
            tender, 'lots', resource_item_id=tender_id
        )

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################

    def create_tender(self, tender):
        return self.create_resource_item(self.prefix_path, tender)

    def create_question(self, tender, question, tender_id=None):
        return self.create_resource_item_subitem(
            tender, question, 'questions', resource_item_id=tender_id
        )

    def create_bid(self, tender, bid, tender_id=None):
        return self.create_resource_item_subitem(
            tender, bid, 'bids', resource_item_id=tender_id
        )

    def create_lot(self, tender, lot, tender_id=None):
        return self.create_resource_item_subitem(
            tender, lot, 'lots', resource_item_id=tender_id
        )

    def create_award(self, tender, award, tender_id=None):
        return self.create_resource_item_subitem(
            tender, award, 'awards', resource_item_id=tender_id
        )

    def create_cancellation(self, tender, cancellation, tender_id=None):
        return self.create_resource_item_subitem(
            tender, cancellation, 'cancellations', resource_item_id=tender_id
        )

    def create_complaint(self, tender, complaint, tender_id=None):
        return self.create_resource_item_subitem(
            tender, complaint, 'complaints', resource_item_id=tender_id
        )

    def create_award_complaint(self, tender, complaint, award_id,
                               tender_id=None):
        depth_path = 'awards/{}'.format(award_id)
        return self.create_resource_item_subitem(
            tender, complaint, 'complaints', depth_path=depth_path,
            resource_item_id=tender_id
        )

    def create_thin_document(self, tender, document_data, tender_id=None):
        return self.create_resource_item_subitem(
            tender, document_data, 'documents', resource_item_id=tender_id
        )

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    def get_tender(self, tender_id):
        return self.get_resource_item(tender_id)

    def get_question(self, tender, question_id, tender_id=None):
        depth_path = 'questions'
        return self.get_resource_item_submitem(
            tender, question_id, depth_path=depth_path,
            resource_item_id=tender_id
        )

    def get_bid(self, tender, bid_id, access_token=None, tender_id=None):
        depth_path = 'bids'
        return self.get_resource_item_submitem(
            tender, bid_id, depth_path=depth_path, access_token=access_token,
            resource_item_id=tender_id
        )

    def get_lot(self, tender, lot_id, tender_id=None):
        depth_path = 'lots'
        return self.get_resource_item_submitem(
            tender, lot_id, depth_path=depth_path, resource_item_id=tender_id
        )

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################

    def patch_tender(self, tender, tender_id=None):
        return self.patch_resource_item(tender, resource_item_id=tender_id)

    def patch_question(self, tender, question, tender_id=None,
                       question_id=None):
        return self.patch_resource_item_subitem(
            tender, question, 'questions', resource_item_id=tender_id,
            subitem_id=question_id
        )

    def patch_bid(self, tender, bid, tender_id=None, bid_id=None):
        return self.patch_resource_item_subitem(
            tender, bid, 'bids', resource_item_id=tender_id, subitem_id=bid_id
        )

    def patch_bid_document(self, tender, document_data, bid_id,
                           document_id=None, tender_id=None):
        depth_path = 'bids/{}'.format(bid_id)
        return self.patch_resource_item_subitem(
            tender, document_data, 'documents', subitem_id=document_id,
            depth_path=depth_path, resource_item_id=tender_id
        )

    def patch_award(self, tender, award, tender_id=None, award_id=None):
        return self.patch_resource_item_subitem(
            tender, award, 'awards', resource_item_id=tender_id,
            subitem_id=award_id
        )

    def patch_award_document(self, tender, document_data, award_id,
                             document_id=None, tender_id=None):
        depth_path = 'awards/{}'.format(award_id)
        return self.patch_resource_item_subitem(
            tender, document_data, 'documents', resource_item_id=tender_id,
            subitem_id=document_id, depth_path=depth_path
        )

    def patch_cancellation(self, tender, cancellation, tender_id=None,
                           cancellation_id=None):
        return self._patch_obj_resource_item(
            tender, cancellation, 'cancellations', subitem_id=cancellation_id,
            resource_item_id=tender_id
        )

    def patch_cancellation_document(self, tender, cancellation,
                                    cancellation_id, cancellation_doc_id=None,
                                    tender_id=None):
        depth_path = 'cancellations/{}'.format(cancellation_id)
        return self.patch_resource_item_subitem(
            tender, cancellation, 'documents', subitem_id=cancellation_doc_id,
            resource_item_id=tender_id, depth_path=depth_path
        )

    def patch_complaint(self, tender, complaint, tender_id=None,
                        complaint_id=None):
        return self.patch_resource_item_subitem(
            tender, complaint, 'complaints', subitem_id=complaint_id,
            resource_item_id=tender_id
        )

    def patch_award_complaint(self, tender, complaint, award_id,
                              tender_id=None, complaint_id=None):
        depth_path = 'awards/{}'.format(award_id)
        return self.patch_resource_item_subitem(
            tender, complaint, 'complaints', resource_item_id=tender_id,
            subitem_id=complaint_id,
        )

    def patch_lot(self, tender, lot, lot_id=None, tender_id=None):
        return self.patch_resource_item_subitem(
            tender, lot, 'lots', subitem_id=lot_id, resource_item_id=tender_id
        )

    def patch_qualification(self, tender, qualification, qualification_id=None,
                            tender_id=None):
        return self.patch_resource_item_subitem(
            tender, qualification, 'qualifications',
            resource_item_id=tender_id, subitem_id=qualification_id
        )

    def patch_contract(self, tender, contract, contract_id=None,
                       tender_id=None):
        return self.patch_resource_item_subitem(
            tender, contract, 'contracts', subitem_id=contract_id,
            resource_item_id=tender_id
        )

    def patch_contract_document(self, tender, document_data,
                                contract_id, document_id=None, tender_id=None):
        depth_path = 'contracts/{}'.format(contract_id)
        return self.patch_resource_item_subitem(
            tender, document_data, 'documents', subitem_id=document_id,
            resource_item_id=tender_id
        )

    ###########################################################################
    #             UPLOAD FILE API METHODS
    ###########################################################################

    def upload_bid_document(self, file_, tender, bid_id, doc_type='documents',
                            use_ds_client=True, doc_registration=True,
                            tender_id=None):
        depth_path = 'bids/{}'.format(bid_id)
        return self.upload_document(file_,)
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
            method='PUT',
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
                method='PUT',
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
                              use_ds_client=True, doc_registration=True,
                              doc_type='documents'):
        return self._upload_resource_file(
            '{}/{}/awards/{}/{}'.format(
                self.prefix_path,
                tender.data.id,
                award_id,
                doc_type
            ),
            file_=file_,
            headers={'X-Access-Token': self._get_access_token(tender)},
            use_ds_client=use_ds_client,
            doc_registration=doc_registration
        )

    @verify_file
    def upload_contract_document(self, file_, tender, contract_id,
                                 use_ds_client=True, doc_registration=True):
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

    def sync_tenders(self, params=None, extra_headers=None):
        _params = (params or {}).copy()
        _params['feed'] = 'changes'
        self.headers.update(extra_headers or {})

        response = self.request('GET', self.prefix_path,
                                params_dict=_params)
        if response.status_code == 200:
            tender_list = munchify(loads(response.text))
            return tender_list

    @retry(stop_max_attempt_number=5)
    def get_tender(self, id, extra_headers=None):
        self.headers.update(extra_headers or {})
        return super(TendersClientSync, self).get_tender(id)


class EDRClient(APITemplateClient):
    """ Client for validate members by EDR """

    host_url = 'https://api-sandbox.openprocurement.org'
    api_version = '2.0'

    def __init__(self, host_url=None, api_version=None, username=None,
                 password=None):
        super(EDRClient, self).__init__(login_pass=(username, password))
        self.host_url = host_url or self.host_url
        self.api_version = api_version or self.api_version

    def verify_member(self, edrpou, extra_headers=None):
        self.headers.update(extra_headers or {})
        response = self.request(
            'GET',
            '{}/api/{}/verify'.format(self.host_url, self.api_version),
            params_dict={'id': edrpou}
        )
        if response.status_code == 200:
            return munchify(loads(response.text))
        raise InvalidResponse(response)
