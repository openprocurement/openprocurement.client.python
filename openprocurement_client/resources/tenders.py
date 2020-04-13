# -*- coding: utf-8 -*-
import logging

from retrying import retry
from zope.deprecation import deprecation

from openprocurement_client.clients import (APIResourceClient,
                                            APIResourceClientSync)
from openprocurement_client.constants import (AUCTIONS, AWARDS, BIDS, CANCELLATIONS,
                                              COMPLAINTS, CONTRACTS, DOCUMENTS, ITEMS,
                                              LOTS, PROLONGATIONS, QUALIFICATIONS, QUESTIONS,
                                              TENDERS, AGREEMENTS, PLANS, PUSH)


LOGGER = logging.getLogger(__name__)


class CreateTenderClient(APIResourceClient):
    """client only for tender creation"""
    resource = PLANS

    def create_tender(self, plan_id, tender, access_token=None):
        return self.create_resource_item_subitem(plan_id, tender, TENDERS, access_token=access_token)


class CreatePaymentClient(APIResourceClient):
    """client only for payment creation"""
    resource = PUSH

    def create_payment(self, payment):
        return self.create_resource_item(payment)

    def _obtain_cookie(self):
        pass


class TendersClient(APIResourceClient):
    """client for tenders"""
    resource = TENDERS

    ###########################################################################
    #                         CREATE ITEM API METHODS
    ###########################################################################

    @deprecation.deprecate("use create_resource_item_subitem instead.")
    def _create_tender_resource_item(self, tender, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, tender.data.id, items_name),
            item_obj,
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    def create_tender(self, tender):
        return self.create_resource_item(tender)

    def create_question(self, tender_id, question, access_token=None):
        return self.create_resource_item_subitem(
            tender_id, question, QUESTIONS, access_token=access_token
        )

    def create_bid(self, tender_id, bid, access_token=None):
        return self.create_resource_item_subitem(
            tender_id, bid, BIDS, access_token=access_token
        )

    def create_lot(self, tender_id, lot, access_token=None):
        return self.create_resource_item_subitem(
            tender_id, lot, LOTS, access_token=access_token
        )

    def create_award(self, tender_id, award, access_token=None):
        return self.create_resource_item_subitem(
            tender_id, award, AWARDS, access_token=access_token
        )

    def create_cancellation(self, tender_id, cancellation, access_token=None):
        return self.create_resource_item_subitem(
            tender_id, cancellation, CANCELLATIONS, access_token=access_token
        )

    def create_complaint(self, tender_id, complaint, access_token=None):
        return self.create_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, access_token=access_token
        )

    def create_award_complaint(self, tender_id, complaint, award_id,
                               access_token=None):
        depth_path = '{}/{}'.format(AWARDS, award_id)
        return self.create_resource_item_subitem(
            tender_id, complaint, COMPLAINTS,
            depth_path=depth_path, access_token=access_token
        )

    def create_qualification_complaint(self, tender_id, complaint, qualification_id, access_token=None):
        depth_path = '{}/{}'.format(QUALIFICATIONS, qualification_id)
        return self.create_resource_item_subitem(
            tender_id, complaint, COMPLAINTS,
            depth_path=depth_path, access_token=access_token
        )

    def create_cancellations_complaint(self, tender_id, complaint, cancellation_id, access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.create_resource_item_subitem(
            tender_id, complaint, COMPLAINTS,
            depth_path=depth_path, access_token=access_token
        )

    def create_thin_document(self, tender_id, document_data, access_token=None):
        return self.create_resource_item_subitem(
            tender_id, document_data, DOCUMENTS, access_token=access_token
        )

    def create_item(self, tender_id, item, access_token=None):
        return self.create_resource_item_subitem(tender_id, item, ITEMS, access_token=access_token)

    def create_prolongation(self, tender_id, contract_id, prolongation_data, access_token=None):
        depth_path = '{}/{}'.format(CONTRACTS, contract_id)
        return self.create_resource_item_subitem(
            tender_id, prolongation_data, PROLONGATIONS, depth_path=depth_path, access_token=access_token
        )

    ###########################################################################
    #                        GET ITEMS LIST API METHODS
    ###########################################################################

    @deprecation.deprecate("use _get_resource_item instead.")
    def _get_tender_resource_list(self, tender, items_name):
        return self._get_resource_item(
            '{}/{}/{}'.format(self.prefix_path, tender.data.id, items_name),
            headers={'X-Access-Token': self._get_access_token(tender)}
        )

    @retry(stop_max_attempt_number=5)
    def get_tenders(self, params=None, feed='changes'):
        return self.get_resource_items(params=params, feed=feed)

    def get_latest_tenders(self, date):
        return self.get_latest_resource_items(date)

    def get_questions(self, tender_id, access_token=None):
        return self.get_resource_item_subitem(tender_id, QUESTIONS, access_token=access_token)

    def get_documents(self, tender_id, access_token=None):
        return self.get_resource_item_subitem(tender_id, DOCUMENTS, access_token=access_token)

    def get_awards_documents(self, tender_id, award_id, access_token=None):
        return self.get_resource_item_subitem(
            tender_id, DOCUMENTS, depth_path='{}/{}'.format(AWARDS, award_id),
            access_token=access_token
        )

    def get_qualification_documents(self, tender_id, qualification_id, access_token=None):
        return self.get_resource_item_subitem(
            tender_id, DOCUMENTS,
            depth_path='{}/{}'.format(QUALIFICATIONS, qualification_id),
            access_token=access_token
        )

    def get_awards(self, tender_id, access_token=None):
        return self.get_resource_item_subitem(tender_id, AWARDS, access_token=access_token)

    def get_lots(self, tender_id, access_token=None):
        return self.get_resource_item_subitem(tender_id, LOTS, access_token=access_token)

    ###########################################################################
    #                           GET ITEM API METHODS
    ###########################################################################

    @deprecation.deprecate("use get_resource_item_subitem instead.")
    def _get_tender_resource_item(self, tender, item_id, items_name,
                                  access_token=None):
        access_token = access_token or self._get_access_token(tender)
        headers = {'X-Access-Token': access_token}
        return self._get_resource_item(
            '{}/{}/{}/{}'.format(self.prefix_path, tender.data.id, items_name, item_id),
            headers=headers
        )

    def get_tender(self, tender_id):
        return self.get_resource_item(tender_id)

    def get_question(self, tender_id, question_id, access_token=None):
        return self.get_resource_item_subitem(
            tender_id, question_id, depth_path=QUESTIONS,
            access_token=access_token
        )

    def get_bid(self, tender_id, bid_id, access_token=None):
        return self.get_resource_item_subitem(
            tender_id, bid_id, depth_path=BIDS, access_token=access_token
        )

    def get_lot(self, tender_id, lot_id, access_token=None):
        return self.get_resource_item_subitem(
            tender_id, lot_id, depth_path=LOTS, access_token=access_token
        )

    ###########################################################################
    #                        PATCH ITEM API METHODS
    ###########################################################################

    def patch_tender(self, tender_id, patch_data={}, access_token=None):
        return self.patch_resource_item(tender_id, patch_data, access_token=access_token)

    def patch_question(self, tender_id, question, question_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, question, QUESTIONS,
            subitem_id=question_id, access_token=access_token
        )

    def patch_bid(self, tender_id, bid, bid_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, bid, BIDS, subitem_id=bid_id, access_token=access_token
        )

    def patch_bid_document(self, tender_id, document_data, bid_id, document_id, access_token=None):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.patch_resource_item_subitem(
            tender_id, document_data, DOCUMENTS, subitem_id=document_id,
            depth_path=depth_path, access_token=access_token
        )

    def patch_award(self, tender_id, award, award_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, award, AWARDS, subitem_id=award_id,
            access_token=access_token
        )

    def patch_award_document(self, tender_id, document_data, award_id, document_id, access_token=None):
        depth_path = '{}/{}'.format(AWARDS, award_id)
        return self.patch_resource_item_subitem(
            tender_id, document_data, DOCUMENTS, subitem_id=document_id,
            depth_path=depth_path, access_token=access_token
        )

    def patch_qualification_complaint(self, tender_id, complaint, qualification_id, complaint_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, subitem_id=complaint_id,
            depth_path='{}/{}'.format(QUALIFICATIONS, qualification_id),
            access_token=access_token
        )

    def patch_cancellation_complaint(self, tender_id, complaint, cancellation_id, complaint_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, subitem_id=complaint_id,
            depth_path='{}/{}'.format(CANCELLATIONS, cancellation_id),
            access_token=access_token
        )

    def patch_cancellation(self, tender_id, cancellation, cancellation_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, cancellation, CANCELLATIONS,
            subitem_id=cancellation_id, access_token=access_token
        )

    def patch_cancellation_document(self, tender_id, cancellation,
                                    cancellation_id, cancellation_doc_id,
                                    access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.patch_resource_item_subitem(
            tender_id, cancellation, DOCUMENTS,
            subitem_id=cancellation_doc_id, depth_path=depth_path,
            access_token=access_token
        )

    def patch_complaint(self, tender_id, complaint, complaint_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, subitem_id=complaint_id,
            access_token=access_token
        )

    def patch_award_complaint(self, tender_id, complaint, award_id, complaint_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, subitem_id=complaint_id,
            depth_path='{}/{}'.format(AWARDS, award_id),
            access_token=access_token
        )

    def patch_cancellation_complaint(self, tender_id, complaint, cancellation_id, complaint_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, subitem_id=complaint_id,
            depth_path='{}/{}'.format(CANCELLATIONS, cancellation_id),
            access_token=access_token
        )

    def patch_qualification_complaint(self, tender_id, complaint, qualification_id, complaint_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, complaint, COMPLAINTS, subitem_id=complaint_id,
            depth_path='{}/{}'.format(QUALIFICATIONS, qualification_id),
            access_token=access_token
        )

    def patch_lot(self, tender_id, lot, lot_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, lot, LOTS, subitem_id=lot_id, access_token=access_token
        )

    def patch_qualification(self, tender_id, qualification, qualification_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, qualification, QUALIFICATIONS,
            subitem_id=qualification_id, access_token=access_token
        )

    def patch_contract(self, tender_id, contract, contract_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, contract, CONTRACTS, subitem_id=contract_id,
            access_token=access_token
        )

    def patch_contract_document(self, tender_id, document_data, contract_id,
                                document_id, access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, document_data, DOCUMENTS,
            subitem_id=document_id,
            depth_path='{}/{}'.format(CONTRACTS, contract_id),
            access_token=access_token
        )

    def patch_auction(self, tender_id, auction, auction_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, auction, AUCTIONS, subitem_id=auction_id, access_token=access_token
        )

    def patch_item(self, tender_id, item, item_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, item, ITEMS, subitem_id=item_id, access_token=access_token
        )

    def patch_agreement(self, tender_id, agreement, agreement_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, agreement, AGREEMENTS,
            subitem_id=agreement_id,
            access_token=access_token
        )

    def patch_agreement_contract(self, tender_id, agreement_id, contract, contract_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, contract, CONTRACTS,
            subitem_id=contract_id,
            depth_path='{}/{}'.format(AGREEMENTS, agreement_id),
            access_token=access_token
        )

    def patch_prolongation(self, tender_id, contract_id, prolongation_id, data, access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, data, PROLONGATIONS,
            subitem_id=prolongation_id,
            depth_path='{}/{}'.format(CONTRACTS, contract_id),
            access_token=access_token
        )

    def patch_prolongation_document(self, tender_id, document_data, contract_id, prolongation_id,
                                    document_id='', access_token=None):
        return self.patch_resource_item_subitem(
            tender_id, document_data, DOCUMENTS,
            subitem_id=document_id,
            depth_path="{}/{}/{}/{}".format(CONTRACTS, contract_id, PROLONGATIONS, prolongation_id),
            access_token=access_token
        )

    ###########################################################################
    #                          UPLOAD FILE API METHODS
    ###########################################################################

    def upload_auction_document(self, file_, tender_id, auction_id, doc_type, use_ds_client=True,
                                doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(AUCTIONS, auction_id)
        return self.upload_document(file_, tender_id,
                                    doc_type=doc_type,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_award_document(self, file_, tender_id, award_id, use_ds_client=True,
                              doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(AWARDS, award_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_award_complaint_document(self, file_, tender_id, award_id, complaint_id, use_ds_client=True,
                                        doc_registration=True, access_token=None):
        depth_path = '{}/{}/{}/{}'.format(AWARDS, award_id, COMPLAINTS, complaint_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_bid_document(self, file_, tender_id, bid_id, doc_type=None, use_ds_client=True,
                            doc_registration=True, access_token=None, subitem_name=DOCUMENTS):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.upload_document(file_, tender_id,
                                    subitem_name=subitem_name,
                                    doc_type=doc_type,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_cancellation_document(self, file_, tender_id, cancellation_id, use_ds_client=True,
                                     doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_cancellation_complaint_document(self, file_, tender_id, cancellation_id, complaint_id, use_ds_client=True,
                                        doc_registration=True, access_token=None):
        depth_path = '{}/{}/{}/{}'.format(CANCELLATIONS, cancellation_id, COMPLAINTS, complaint_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_complaint_document(self, file_, tender_id, complaint_id, use_ds_client=True,
                                  doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(COMPLAINTS, complaint_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_contract_document(self, file_, tender_id, contract_id, use_ds_client=True,
                                 doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(CONTRACTS, contract_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_qualification_document(self, file_, tender_id, qualification_id, use_ds_client=True,
                                      doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(QUALIFICATIONS, qualification_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_qualification_complaint_document(self, file_, tender_id, qualification_id, complaint_id, use_ds_client=True,
                                        doc_registration=True, access_token=None):
        depth_path = '{}/{}/{}/{}'.format(QUALIFICATIONS, qualification_id, COMPLAINTS, complaint_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    def upload_prolongation_document(self, file_, tender_id, contract_id, prolongation_id, use_ds_client=True,
                                     doc_registration=True, access_token=None):
        depth_path = "{}/{}/{}/{}".format(CONTRACTS, contract_id, PROLONGATIONS, prolongation_id)
        return self.upload_document(file_, tender_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    ###########################################################################
    #                            UPDATE FILE API METHODS
    ###########################################################################

    def update_bid_document(self, file_, tender_id, bid_id, document_id, doc_type=None, use_ds_client=True,
                            doc_registration=True, access_token=None, subitem_name=DOCUMENTS):
        depth_path = '{}/{}'.format(BIDS, bid_id)
        return self.update_document(file_, tender_id, document_id,
                                    doc_type=doc_type,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path,
                                    access_token=access_token,
                                    subitem_name=subitem_name)

    def update_cancellation_document(self, file_, tender_id, cancellation_id, document_id, doc_type=None,
                                     use_ds_client=True, doc_registration=True, access_token=None):
        depth_path = '{}/{}'.format(CANCELLATIONS, cancellation_id)
        return self.update_document(file_, tender_id, document_id,
                                    doc_type=doc_type,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    depth_path=depth_path, access_token=access_token)

    ###########################################################################
    #             DELETE ITEMS LIST API METHODS
    ###########################################################################

    def delete_bid(self, tender_id, bid_id, access_token=None):
        if isinstance(bid_id, basestring):
            bid_id = bid_id
            access_token = access_token
        else:
            access_token = getattr(getattr(bid_id, 'access', ''), 'token', '')
            bid_id = bid_id['data']['id']
        return self.delete_resource_item_subitem(tender_id, BIDS, bid_id, access_token=access_token)

    def delete_lot(self, tender_id, lot_id, access_token=None):
        if isinstance(tender_id, basestring):
            tender_id = tender_id
            access_token = access_token
        else:
            access_token = self._get_access_token(tender_id)
            tender_id = tender_id['data']['id']
        if not isinstance(lot_id, basestring):
            lot_id = lot_id['data']['id']
        return self.delete_resource_item_subitem(tender_id, LOTS, lot_id, access_token=access_token)

    ###########################################################################


class PaymentClient(CreatePaymentClient):
    """client for payment push only"""


class Client(TendersClient):
    """client for tenders for backward compatibility"""


class TendersClientSync(APIResourceClientSync):
    resource = TENDERS

    sync_tenders = APIResourceClientSync.sync_resource_items

    get_tender = APIResourceClientSync.get_resource_item


class TenderCreateClient(CreateTenderClient):
    """client for tender publication only"""
