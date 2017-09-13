# -*- coding: utf-8 -*-
from openprocurement_client.clients import (
    APIResourceClient, APIResourceClientSync
)
from openprocurement_client.constants import (
    AWARDS, BIDS, CANCELLATIONS, COMPLAINTS, CONTRACTS, DOCUMENTS,
    LOTS, QUALIFICATIONS, QUESTIONS
)
from retrying import retry


class TendersClient(APIResourceClient):
    """client for tenders"""

    def __init__(self, *args, **kwargs):
        super(TendersClient, self).__init__(*args, **kwargs)

    ###########################################################################
    #                         CREATE ITEM API METHODS
    ###########################################################################

    def create_tender(self, tender):
        return self.create_resource_item(tender)

    def create_question(self, tender_id, question):
        return self.create_resource_item_subitem(
            tender_id, question, QUESTIONS
        )

    def create_bid(self, tender_id, bid):
        return self.create_resource_item_subitem(tender_id, bid, BIDS)

    def create_lot(self, tender_id, lot):
        return self.create_resource_item_subitem(tender_id, lot, LOTS)

    def create_award(self, tender_id, award):
        return self.create_resource_item_subitem(tender_id, award, AWARDS)

    def create_cancellation(self, tender_id, cancellation):
        return self.create_resource_item_subitem(
            tender_id, cancellation, CANCELLATIONS
        )

    def create_complaint(self, tender_id, complaint):
        return self.create_resource_item_subitem(
            tender_id, complaint, COMPLAINTS
        )

    def create_award_complaint(self, tender_id, complaint, award_id):
        depth_path = '{}/{}'.format(AWARDS, award_id)
        return self.create_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, depth_path=depth_path
        )

    def create_thin_document(self, tender_id, document_data):
        return self.create_resource_item_subitem(
            tender_id, document_data, DOCUMENTS
        )

    ###########################################################################
    #                        GET ITEMS LIST API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_tenders(self, params=None, feed='changes'):
        return self.get_resource_items(params=params, feed=feed)

    def get_latest_tenders(self, date):
        return self.get_latest_resource_items(date)

    def get_questions(self, tender_id):
        return self.get_resource_item_subitem(tender_id, QUESTIONS)

    def get_documents(self, tender_id):
        return self.get_resource_item_subitem(tender_id, DOCUMENTS)

    def get_awards_documents(self, tender_id, award_id):
        return self.get_resource_item_subitem(
            tender_id, DOCUMENTS, depth_path='{}/{}'.format(AWARDS, award_id)
        )

    def get_qualification_documents(self, tender_id, qualification_id):
        return self.get_resource_item_subitem(
            tender_id, DOCUMENTS,
            depth_path='{}/{}'.format(QUALIFICATIONS, qualification_id)
        )

    def get_awards(self, tender_id):
        return self.get_resource_item_subitem(tender_id, AWARDS)

    def get_lots(self, tender_id):
        return self.get_resource_item_subitem(tender_id, LOTS)

    ###########################################################################
    #                           GET ITEM API METHODS
    ###########################################################################

    def get_tender(self, tender_id):
        return self.get_resource_item(tender_id)

    def get_question(self, tender_id, question_id):
        return self.get_resource_item_subitem(
            tender_id, question_id, depth_path=QUESTIONS
        )

    def get_bid(self, tender_id, bid_id, access_token=None):
        return self.get_resource_item_subitem(
            tender_id, bid_id, depth_path=BIDS, access_token=access_token
        )

    def get_lot(self, tender_id, lot_id):
        return self.get_resource_item_subitem(
            tender_id, lot_id, depth_path=LOTS
        )

    ###########################################################################
    #                        PATCH ITEM API METHODS
    ###########################################################################

    def patch_tender(self, tender_id, patch_data):
        return self.patch_resource_item(tender_id, patch_data)

    def patch_question(self, tender_id, question, question_id):
        return self.patch_resource_item_subitem(
            tender_id, question, QUESTIONS, subitem_id=question_id
        )

    def patch_bid(self, tender_id, bid, bid_id):
        return self.patch_resource_item_subitem(
            tender_id, bid, BIDS, subitem_id=bid_id
        )

    def patch_bid_document(self, tender_id, document_data, bid_id,
                           document_id):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.patch_resource_item_subitem(
            tender_id, document_data, DOCUMENTS, subitem_id=document_id,
            depth_path=depth_path
        )

    def patch_award(self, tender_id, award, award_id):
        return self.patch_resource_item_subitem(
            tender_id, award, AWARDS, subitem_id=award_id
        )

    def patch_award_document(self, tender_id, document_data, award_id,
                             document_id):
        depth_path = '{}/{}'.format(AWARDS, award_id)
        return self.patch_resource_item_subitem(
            tender_id, document_data, DOCUMENTS, subitem_id=document_id,
            depth_path=depth_path
        )

    def patch_cancellation(self, tender_id, cancellation, cancellation_id):
        return self.patch_resource_item_subitem(
            tender_id, cancellation, CANCELLATIONS,
            subitem_id=cancellation_id
        )

    def patch_cancellation_document(self, tender_id, cancellation,
                                    cancellation_id, cancellation_doc_id):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.patch_resource_item_subitem(
            tender_id, cancellation, DOCUMENTS,
            subitem_id=cancellation_doc_id, depth_path=depth_path
        )

    def patch_complaint(self, tender_id, complaint, complaint_id):
        return self.patch_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, subitem_id=complaint_id
        )

    def patch_award_complaint(self, tender_id, complaint, award_id,
                              complaint_id):
        return self.patch_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, subitem_id=complaint_id,
            depth_path='{}/{}'.format(AWARDS, award_id)
        )

    def patch_lot(self, tender_id, lot, lot_id):
        return self.patch_resource_item_subitem(
            tender_id, lot, LOTS, subitem_id=lot_id
        )

    def patch_qualification(self, tender_id, qualification, qualification_id):
        return self.patch_resource_item_subitem(
            tender_id, qualification, QUALIFICATIONS,
            subitem_id=qualification_id
        )

    def patch_contract(self, tender_id, contract, contract_id):
        return self.patch_resource_item_subitem(
            tender_id, contract, CONTRACTS, subitem_id=contract_id
        )

    def patch_contract_document(self, tender_id, document_data, contract_id,
                                document_id):
        return self.patch_resource_item_subitem(
            tender_id, document_data, DOCUMENTS, subitem_id=document_id,
            depth_path='{}/{}'.format(CONTRACTS, contract_id)
        )

    ###########################################################################
    #                          UPLOAD FILE API METHODS
    ###########################################################################

    def upload_bid_document(self, file_, tender_id, bid_id,
                            doc_registration=True, access_token=None,
                            doc_type=DOCUMENTS):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.upload_document(
            file_, tender_id, doc_registration,
            access_token, depth_path, doc_type
        )

    def upload_cancellation_document(self, file_, tender_id, cancellation_id,
                                     doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.upload_document(file_, tender_id,
                                    doc_registration=doc_registration,
                                    access_token=access_token,
                                    depth_path=depth_path)

    def upload_complaint_document(self, file_, tender_id, complaint_id,
                                  doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(COMPLAINTS, complaint_id)
        return self.upload_document(file_, tender_id,
                                    doc_registration=doc_registration,
                                    access_token=access_token,
                                    depth_path=depth_path)

    def upload_award_complaint_document(self, file_, tender_id, award_id,
                                        complaint_id,
                                        doc_registration=True,
                                        access_token=None):
        depth_path = '{}/{}/{}/{}'.format(AWARDS, award_id,
                                          COMPLAINTS, complaint_id)
        return self.upload_document(file_, tender_id,
                                    doc_registration=doc_registration,
                                    access_token=access_token,
                                    depth_path=depth_path)

    def upload_qualification_document(self, file_, tender_id, qualification_id,
                                      doc_registration=True,
                                      access_token=None):
        depth_path = '{}/{}'.format(QUALIFICATIONS, qualification_id)
        return self.upload_document(file_, tender_id,
                                    doc_registration=doc_registration,
                                    access_token=access_token,
                                    depth_path=depth_path)

    def upload_award_document(self, file_, tender_id, award_id,
                              doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(AWARDS, award_id)
        return self.upload_document(file_, tender_id,
                                    doc_registration=doc_registration,
                                    access_token=access_token,
                                    depth_path=depth_path)

    def upload_contract_document(self, file_, tender_id, contract_id,
                                 doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(CONTRACTS, contract_id)
        return self.upload_document(file_, tender_id, doc_registration,
                                    access_token, depth_path)

    ###########################################################################
    #                            UPDATE FILE API METHODS
    ###########################################################################

    def update_bid_document(self, file_, tender_id, bid_id, document_id,
                            doc_registration=True, access_token=None,
                            doc_type=DOCUMENTS):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.update_document(
            file_, tender_id, document_id, doc_registration,
            access_token, depth_path, doc_type
        )

    def update_cancellation_document(self, file_, tender_id, cancellation_id,
                                     document_id, doc_registration=True,
                                     access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.update_document(
            file_, tender_id, document_id, doc_registration,
            access_token, depth_path
        )

    ###########################################################################
    #             DELETE ITEMS LIST API METHODS
    ###########################################################################

    def delete_bid(self, tender_id, bid_id, access_token=None):
        return self.delete_resource_item_subitem(
            tender_id, BIDS, bid_id, access_token=access_token
        )

    def delete_lot(self, tender_id, lot_id, access_token=None):
        return self.delete_resource_item_subitem(
            tender_id, LOTS, lot_id, access_token=access_token
        )
    ###########################################################################


class Client(TendersClient):
    """client for tenders for backward compatibility"""


class TendersClientSync(APIResourceClientSync):

    sync_tenders = APIResourceClientSync.sync_resource_items

    get_tender = APIResourceClientSync.get_resource_item
