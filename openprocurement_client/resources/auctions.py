# -*- coding: utf-8 -*-
from openprocurement_client.clients import (
    APIResourceClient, APIResourceClientSync
)
from openprocurement_client.constants import (
    AUCTIONS,
    AWARDS,
    BIDS,
    CANCELLATIONS,
    CONTRACTS,
    DOCUMENTS,
    QUESTIONS
)
from retrying import retry


class AuctionsClient(APIResourceClient):
    """client for auctions"""

    resource = AUCTIONS

    ###########################################################################
    #                         CREATE ITEM API METHODS
    ###########################################################################

    def create_auction(self, auction):
        return self.create_resource_item(auction)

    def create_question(self, auction_id, question, access_token=None):
        return self.create_resource_item_subitem(
            auction_id, question, QUESTIONS, access_token=access_token
        )

    def create_bid(self, auction_id, bid, access_token=None):
        return self.create_resource_item_subitem(
            auction_id, bid, BIDS, access_token=access_token
        )

    def create_cancellation(self, auction_id, cancellation,
                            access_token=None):
        return self.create_resource_item_subitem(
            auction_id, cancellation, CANCELLATIONS,
            access_token=access_token
        )

    def create_thin_document(self, auction_id, document_data, access_token=None):
        return self.create_resource_item_subitem(
            auction_id, document_data, DOCUMENTS, access_token=access_token
        )

    ###########################################################################
    #                        GET ITEMS LIST API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_auctions(self, params=None, feed='changes'):
        return self.get_resource_items(params=params, feed=feed)

    def get_latest_auctions(self, date):
        return self.get_latest_resource_items(date)

    def get_questions(self, auction_id, access_token=None):
        return self.get_resource_item_subitem(auction_id, QUESTIONS,
                                              access_token=access_token)

    def get_documents(self, auction_id, access_token=None):
        return self.get_resource_item_subitem(auction_id, DOCUMENTS,
                                              access_token=access_token)

    def get_awards_documents(self, auction_id, award_id, access_token=None):
        return self.get_resource_item_subitem(
            auction_id, DOCUMENTS, depth_path='{}/{}'.format(AWARDS, award_id),
            access_token=access_token
        )

    def get_awards(self, auction_id, access_token=None):
        return self.get_resource_item_subitem(auction_id, AWARDS,
                                              access_token=access_token)

    ###########################################################################
    #                           GET ITEM API METHODS
    ###########################################################################

    def get_auction(self, auction_id):
        return self.get_resource_item(auction_id)

    def get_question(self, auction_id, question_id, access_token=None):
        return self.get_resource_item_subitem(
            auction_id, question_id, depth_path=QUESTIONS,
            access_token=access_token
        )

    def get_bid(self, auction_id, bid_id, access_token=None):
        return self.get_resource_item_subitem(
            auction_id, bid_id, depth_path=BIDS, access_token=access_token
        )

    ###########################################################################
    #                        PATCH ITEM API METHODS
    ###########################################################################

    def patch_auction(self, auction_id, patch_data, access_token=None):
        return self.patch_resource_item(auction_id, patch_data,
                                        access_token=access_token)

    def patch_question(self, auction_id, question, question_id,
                       access_token=None):
        return self.patch_resource_item_subitem(
            auction_id, question, QUESTIONS,
            subitem_id=question_id, access_token=access_token
        )

    def patch_bid(self, auction_id, bid, bid_id, access_token=None):
        return self.patch_resource_item_subitem(
            auction_id, bid, BIDS, subitem_id=bid_id, access_token=access_token
        )

    def patch_bid_document(self, auction_id, document_data, bid_id,
                           document_id, access_token=None):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.patch_resource_item_subitem(
            auction_id, document_data, DOCUMENTS, subitem_id=document_id,
            depth_path=depth_path, access_token=access_token
        )

    def patch_award(self, auction_id, award, award_id, access_token=None):
        return self.patch_resource_item_subitem(
            auction_id, award, AWARDS, subitem_id=award_id,
            access_token=access_token
        )

    def patch_award_document(self, auction_id, document_data, award_id,
                             document_id, access_token=None):
        depth_path = '{}/{}'.format(AWARDS, award_id)
        return self.patch_resource_item_subitem(
            auction_id, document_data, DOCUMENTS, subitem_id=document_id,
            depth_path=depth_path, access_token=access_token
        )

    def patch_cancellation(self, auction_id, cancellation, cancellation_id,
                           access_token=None):
        return self.patch_resource_item_subitem(
            auction_id, cancellation, CANCELLATIONS,
            subitem_id=cancellation_id, access_token=access_token
        )

    def patch_cancellation_document(self, auction_id, cancellation, cancellation_id,
                                    cancellation_doc_id, access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.patch_resource_item_subitem(
            auction_id, cancellation, DOCUMENTS, subitem_id=cancellation_doc_id,
            depth_path=depth_path, access_token=access_token
        )

    def patch_contract(self, auction_id, contract, contract_id, access_token=None):
        return self.patch_resource_item_subitem(
            auction_id, contract, CONTRACTS, subitem_id=contract_id,
            access_token=access_token
        )

    def patch_contract_document(self, auction_id, document_data, contract_id,
                                document_id, access_token=None):
        return self.patch_resource_item_subitem(
            auction_id, document_data, DOCUMENTS, subitem_id=document_id,
            depth_path='{}/{}'.format(CONTRACTS, contract_id),
            access_token=access_token
        )

    ###########################################################################
    #                          UPLOAD FILE API METHODS
    ###########################################################################

    def upload_bid_document(self, file_, auction_id, bid_id,
                            doc_registration=True, access_token=None,
                            doc_type=DOCUMENTS):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.upload_document(
            file_, auction_id, doc_registration,
            access_token, depth_path, doc_type
        )

    def upload_cancellation_document(self, file_, auction_id, cancellation_id,
                                     doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.upload_document(file_, auction_id,
                                    doc_registration=doc_registration,
                                    access_token=access_token,
                                    depth_path=depth_path)

    def upload_award_document(self, file_, auction_id, award_id,
                              doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(AWARDS, award_id)
        return self.upload_document(file_, auction_id,
                                    doc_registration=doc_registration,
                                    access_token=access_token,
                                    depth_path=depth_path)

    def upload_contract_document(self, file_, auction_id, contract_id,
                                 doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(CONTRACTS, contract_id)
        return self.upload_document(file_, auction_id, doc_registration,
                                    access_token, depth_path)

    ###########################################################################
    #                            UPDATE FILE API METHODS
    ###########################################################################

    def update_bid_document(self, file_, auction_id, bid_id, document_id,
                            doc_registration=True, access_token=None,
                            doc_type=DOCUMENTS):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.update_document(
            file_, auction_id, document_id, doc_registration,
            access_token, depth_path, doc_type
        )

    def update_cancellation_document(self, file_, auction_id, cancellation_id,
                                     document_id, doc_registration=True,
                                     access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.update_document(
            file_, auction_id, document_id, doc_registration,
            access_token, depth_path
        )

    ###########################################################################
    #             DELETE ITEMS LIST API METHODS
    ###########################################################################

    def delete_bid(self, auction_id, bid_id, access_token=None):
        return self.delete_resource_item_subitem(
            auction_id, BIDS, bid_id, access_token=access_token
        )

    ###########################################################################

