from functools import wraps
from iso8601 import parse_date
from munch import munchify
from restkit import BasicAuth, errors, request, Resource
from retrying import retry
from simplejson import dumps, loads
from urlparse import parse_qs, urlparse
import logging

logger = logging.getLogger(__name__)

IGNORE_PARAMS = ('uri', 'path')


def verify_file(fn):
    @wraps(fn)
    def wrapper(self, file_, *args, **kwargs):
        if isinstance(file_, str):
            file_ = open(file_, 'rb')
        if hasattr(file_, 'read'):
            # A file-like object must have 'read' method
            return fn(self, file_, *args, **kwargs)
        else:
            raise TypeError('Expected either a string '
                            'containing a path to file or a '
                            'file-like object, got {}'.format(type(file_)))
    return wrapper


class InvalidResponse(Exception):
    pass


class NoToken(Exception):
    pass


class Client(Resource):
    """docstring for API"""
    def __init__(self, key,
                 host_url="https://api-sandbox.openprocurement.org",
                 api_version='0.8',
                 resource='tenders',
                 params=None,
                 **kwargs):
        super(Client, self).__init__(
            host_url,
            filters=[BasicAuth(key, "")],
            **kwargs
        )
        self.prefix_path = '/api/{}/{}'.format(api_version, resource)
        if not isinstance(params, dict):
            params = {"mode": "_all_"}
        self.params = params
        self.headers = {"Content-Type": "application/json"}
        # To perform some operations (e.g. create a tender)
        # we first need to obtain a cookie. For that reason,
        # here we send a HEAD request to a neutral URL.
        self.head('/api/{}/spore'.format(api_version))

    def request(self, method, path=None, payload=None, headers=None,
                params_dict=None, **params):
        _headers = dict(self.headers)
        _headers.update(headers or {})
        try:
            response = super(Client, self).request(
                method, path=path, payload=payload, headers=_headers,
                params_dict=params_dict, **params
            )
            if 'Set-Cookie' in response.headers:
                self.headers['Cookie'] = response.headers['Set-Cookie']
            return response
        except errors.ResourceNotFound as e:
            if 'Set-Cookie' in e.response.headers:
                self.headers['Cookie'] = e.response.headers['Set-Cookie']
            raise e

    def patch(self, path=None, payload=None, headers=None,
              params_dict=None, **params):
        """ HTTP PATCH

        - payload: string passed to the body of the request
        - path: string  additionnal path to the uri
        - headers: dict, optionnal headers that will
            be added to HTTP request.
        - params: Optionnal parameterss added to the request
        """

        return self.request("PATCH", path=path, payload=payload,
                            headers=headers, params_dict=params_dict, **params)

    def delete(self, path=None, headers=None):
        """ HTTP DELETE
        - path: string  additionnal path to the uri
        - headers: dict, optionnal headers that will
            be added to HTTP request.
        - params: Optionnal parameterss added to the request
        """
        return self.request("DELETE", path=path, headers=headers)

    def _update_params(self, params):
        for key in params:
            if key not in IGNORE_PARAMS:
                self.params[key] = params[key]

    ###########################################################################
    #             GET ITEMS LIST API METHODS
    ###########################################################################

    @retry(stop_max_attempt_number=5)
    def get_tenders(self, params={}, feed='changes'):
        params['feed'] = feed
        try:
            self._update_params(params)
            response = self.get(
                self.prefix_path,
                params_dict=self.params)
            if response.status_int == 200:
                tender_list = munchify(loads(response.body_string()))
                self._update_params(tender_list.next_page)
                return tender_list.data

        except errors.ResourceNotFound:
            del self.params['offset']
            raise

        raise InvalidResponse

    def get_latest_tenders(self, date, tender_id):
        iso_dt = parse_date(date)
        dt = iso_dt.strftime("%Y-%m-%d")
        tm = iso_dt.strftime("%H:%M:%S")
        response = self._get_resource_item(
            '{}?offset={}T{}&opt_fields=tender_id&mode=test'.format(
                self.prefix_path,
                dt,
                tm
            )
        )
        if response.status_int == 200:
            tender_list = munchify(loads(response.body_string()))
            self._update_params(tender_list.next_page)
            return tender_list.data
        raise InvalidResponse

    def _get_tender_resource_list(self, tender, items_name):
        return self._get_resource_item(
            '{}/{}/{}'.format(self.prefix_path, tender.data.id, items_name),
            headers={'X-Access-Token':
                     getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def get_questions(self, tender, params={}):
        return self._get_tender_resource_list(tender, "questions")

    def get_documents(self, tender, params={}):
        return self._get_tender_resource_list(tender, "documents")

    def get_awards(self, tender, params={}):
        return self._get_tender_resource_list(tender, "awards")

    def get_lots(self, tender, params={}):
        return self._get_tender_resource_list(tender, "lots")

    ###########################################################################
    #             CREATE ITEM API METHODS
    ###########################################################################
    def _create_resource_item(self, url, payload, headers={}):
        headers.update(self.headers)
        response_item = self.post(
            url, headers=headers, payload=dumps(payload)
        )
        if response_item.status_int == 201:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def _create_tender_resource_item(self, tender, item_obj, items_name):
        return self._create_resource_item(
            '{}/{}/{}'.format(self.prefix_path, tender.data.id, items_name),
            item_obj,
            headers={'X-Access-Token':
                     getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def create_tender(self, tender):
        return self._create_resource_item(self.prefix_path, tender)

    def create_question(self, tender, question):
        return self._create_tender_resource_item(tender, question, "questions")

    def create_bid(self, tender, bid):
        return self._create_tender_resource_item(tender, bid, "bids")

    def create_lot(self, tender, lot):
        return self._create_tender_resource_item(tender, lot, "lots")

    def create_award(self, tender, award):
        return self._create_tender_resource_item(tender, award, "awards")

    def create_cancellation(self, tender, cancellation):
        return self._create_tender_resource_item(tender, cancellation, "cancellations")

    ###########################################################################
    #             GET ITEM API METHODS
    ###########################################################################

    def _get_resource_item(self, url, headers={}):
        headers.update(self.headers)
        response_item = self.get(url, headers=headers)
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def get_tender(self, id):
        return self._get_resource_item('{}/{}'.format(self.prefix_path, id))

    def _get_tender_resource_item(self, tender_id, item_id, items_name,
                                  access_token=None):
        logger.info("_get_tender_resource_item is deprecated. In next update this function will takes tender_id instead tender.")
        if  not isinstance(tender_id, basestring):
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._get_resource_item(
            '{}/{}/{}/{}'.format(self.prefix_path,
                                 tender_id
                                 items_name,
                                 item_id),
            headers={'X-Access-Token': access_token}
        )

    def get_question(self, tender_id, question_id, access_token=None):
        logger.info("get_question is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._get_tender_resource_item(tender_id, question_id, "questions", access_token)

     def get_bid(self, tender_id, bid_id, access_token):
        logger.info("get_bid is deprecated. In next update this function will takes tender_id instead tender.")
        if  not isinstance(tender_id, basestring):
            tender_id = tender_id.data.id
        return self._get_tender_resource_item(tender_id, bid_id, "bids", access_token)

    def get_lot(self, tender_id, lot_id, access_token=None):
        logger.info("get_lot is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._get_tender_resource_item(tender_id, lot_id, "lots", access_token)

    def get_file(self, tender, url, access_token):
        logger.info("get_file is deprecated. In next update this function will no takes tender.")
        parsed_url = urlparse(url)
        if access_token:
            headers = {'X-Access-Token': access_token}
        else:
            raise NoToken

        headers.update(self.headers)
        response_item = self.get(parsed_url.path,
                                 headers=headers,
                                 params_dict=parse_qs(parsed_url.query))

        if response_item.status_int == 302:
            response_obj = request(response_item.headers['location'])
            if response_obj.status_int == 200:
                return response_obj.body_string(), \
                    response_obj.headers['Content-Disposition'] \
                    .split(";")[1].split('"')[1]
        raise InvalidResponse

    ###########################################################################
    #             PATCH ITEM API METHODS
    ###########################################################################

    def _patch_resource_item(self, url, payload, headers={}):
        headers.update(self.headers)
        response_item = self.patch(
            url, headers=headers, payload=dumps(payload)
        )
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def _patch_tender_resource_item(self, tender_id, item_obj, items_name, access_token=None):
        logger.info("_patch_tender_resource_item is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_resource_item(
            '{}/{}/{}/{}'.format(
                self.prefix_path, tender_id, items_name, item_obj['data']['id']
            ),
            payload=item_obj,
            headers={'X-Access-Token':access_token}
        )

    def patch_tender(self, tender):
        return self._patch_resource_item(
            '{}/{}'.format(self.prefix_path, tender["data"]["id"]),
            payload=tender,
            headers={'X-Access-Token':
                     getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def patch_question(self, tender_id, question, access_token=None):
        logger.info("patch_question is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_tender_resource_item(tender_id, question, "questions", access_token)

    def patch_bid(self, tender_id, bid, access_token=None):
        logger.info("patch_bid is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_tender_resource_item(tender_id, bid, "bids", access_token)

    def patch_qualification(self, tender_id, qualification, access_token=None):
        logger.info("patch_qualification is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_tender_resource_item(tender_id, qualification, "qualifications", access_token)

    def patch_award(self, tender_id, award, access_token=None):
        logger.info("patch_award is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_tender_resource_item(tender_id, award, "awards", access_token)

    def patch_cancellation(self, tender_id, cancellation, access_token=None):
        logger.info("patch_cancellation is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_tender_resource_item(tender_id, cancellation, "cancellations", access_token)

    def patch_cancellation_document(self, tender, cancellation_data, cancel_num, doc_num):
        cancel_num = int(cancel_num)
        doc_num = int(doc_num)
        return self._patch_resource_item(
            '{}/{}/{}/{}/documents/{}'.format(
                self.prefix_path, tender.data.id, "cancellations", tender['data']['cancellations'][cancel_num]['id'], tender['data']['cancellations'][cancel_num]['documents'][doc_num]['id']
            ),
            payload=cancellation_data,
            headers={'X-Access-Token':
                     getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def patch_lot(self, tender_id, lot, access_token=None):
        logger.info("patch_lot is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_tender_resource_item(tender_id, lot, "lots", access_token)

    def patch_document(self, tender_id, document, access_token=None):
        logger.info("patch_document is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_tender_resource_item(tender_id, document, "documents", access_token)

    def patch_contract(self, tender_id, contract, access_token=None):
        logger.info("patch_contract is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._patch_tender_resource_item(tender_id, contract, "contracts", access_token)

    ###########################################################################
    #             UPLOAD FILE API METHODS
    ###########################################################################
    def _upload_resource_file(self, url, data, headers={}, method='post'):
        file_headers = {}
        file_headers.update(self.headers)
        file_headers.update(headers)
        file_headers['Content-Type'] = "multipart/form-data"
        response_item = getattr(self, method)(
            url, headers=file_headers, payload=data
        )
        if response_item.status_int in (201, 200):
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    @verify_file
    def upload_document(self, file_, tender_id, access_token=None):
        logger.info("upload_document is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._upload_resource_file(
            '{}/{}/documents'.format(
                self.prefix_path,
                tender_id
            ),
            data={"file": file_},
            headers={'X-Access-Token':access_token}
        )

    @verify_file
    def upload_bid_document(self, file_, tender_id, bid_id, access_token=None):
        logger.info("upload_bid_document is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._upload_resource_file(
            '{}/{}/bids/{}/documents'.format(
                self.prefix_path,
                tender_id,
                bid_id
            ),
            data={"file": file_},
            headers={'X-Access-Token':access_token}}
        )

    @verify_file
    def update_bid_document(self, file_, tender_id, bid_id, document_id, access_token=None):
        logger.info("upload_cancellation_document is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._upload_resource_file(
            '{}/{}/bids/{}/documents/{}'.format(
                self.prefix_path,
                tender_id,
                bid_id,
                document_id
            ),
            data={"file": file_},
            headers={'X-Access-Token':access_token},
            method='put'
        )

    @verify_file
    def upload_cancellation_document(self, file_, tender_id, cancellation_id, access_token=None):
        logger.info("upload_cancellation_document is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._upload_resource_file(
            '{}/{}/cancellations/{}/documents'.format(
                self.prefix_path,
                tender_id,
                cancellation_id
            ),
            data={"file": file_},
            headers={'X-Access-Token':access_token}
        )

    @verify_file
    def update_cancellation_document(self, file_, tender_id, cancellation_id, document_id, access_token=None):
        logger.info("update_cancellation_document is deprecated. In next update this function will takes tender_id and access_token instead tender.")
        if  not isinstance(tender_id, basestring) and not access_token:
            access_token = getattr(getattr(tender_id, 'access', ''), 'token', '')
            tender_id = tender_id.data.id
        return self._upload_resource_file(
            '{}/{}/cancellations/{}/documents/{}'.format(
                self.prefix_path,
                tender_id,
                cancellation_id,
                document_id
            ),
            data={"file": file_},
            headers={'X-Access-Token':access_token},
            method='put'
        )

    ###########################################################################
    #             DELETE ITEMS LIST API METHODS
    ###########################################################################

    def _delete_resource_item(self, url, headers={}):
        response_item = self.delete(url, headers=headers)
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def delete_bid(self, tender_id, bid_id, access_token=None):
        logger.info("delete_bid is deprecated. In next update this function will takes tender_id, bid_id and access_token instead tender and bid.")
        if not isinstance(bid_id, basestring) and not access_token:
            access_token = getattr(getattr(bid_id, 'access', ''), 'token', '')
            bid_id = bid_id.data.id
        if  not isinstance(tender_id, basestring):
            tender_id = tender.data.id
        return self._delete_resource_item(
            '{}/{}/bids/{}'.format(
                self.prefix_path,
                tender_id,
                bid_id
            ),
            headers={'X-Access-Token': access_token}
        )

    def delete_lot(self, tender_id, lot_id, access_token=None):
        logger.info("delete_lot is deprecated. In next update this function will takes tender_id, lot_id and access_token instead tender and lot.")
        if not isinstance(lot_id, basestring) and not access_token:
            access_token = getattr(getattr(lot_id, 'access', ''), 'token', '')
            lot_id = lot_id.data.id
        if  not isinstance(tender_id, basestring):
            tender_id = tender.data.id
        return self._delete_resource_item(
            '{}/{}/lots/{}'.format(
                self.prefix_path,
                tender_id,
                lot_id
            ),
            headers={'X-Access-Token':access_token}
        )
    ###########################################################################
