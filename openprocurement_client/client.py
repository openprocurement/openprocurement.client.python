# from gevent import monkey
# monkey.patch_all()
from restkit import Resource, BasicAuth
from munch import munchify
from simplejson import loads, dumps

IGNORE_PARAMS = ('uri', 'path',)


class InvalidResponse(Exception):
    pass


class Client(Resource):
    """docstring for API"""
    def __init__(self, key):
        super(Client, self).__init__(
            "https://api-sandbox.openprocurement.org",
            filters=[BasicAuth(key, "")]
        )
        self.prefix_path = '/api/0.7/tenders'
        self.params = {"mode": "_all_"}
        self.headers = {"Content-Type": "application/json"}

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

    def _update_params(self, params):
        for key in params:
            if key not in IGNORE_PARAMS:
                self.params[key] = params[key]

    ############################################################################
    #             GET ITEMS LIST API METHODS
    ############################################################################

    def get_tenders(self, params={}):
        self._update_params(params)
        response = self.get(
            '/api/0.7/tenders',
            params_dict=self.params)
        if response.status_int == 200:
            tender_list = munchify(loads(response.body_string()))
            self._update_params(tender_list.next_page)
            return tender_list.data
        raise InvalidResponse

    def _get_tender_resource_list(self, tender, items_name):
        return self._get_resource_item(
            self.prefix_path + '/{}/{}'.format(tender.data.id, items_name),
            headers={'X-Access-Token': getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def get_questions(self, tender, params={}):
        return self._get_tender_resource_list(tender, "questions")

    def get_documents(self, tender, params={}):
        return self._get_tender_resource_list(tender, "documents")

    def get_awards(self, tender, params={}):
        return self._get_tender_resource_list(tender, "awards")

    ############################################################################
    #             CREATE ITEM API METHODS
    ############################################################################
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
            self.prefix_path + '/{}/'.format(tender.data.id) + items_name,
            item_obj,
            headers={'X-Access-Token': getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def create_tender(self, tender):
        return self._create_resource_item(self.prefix_path, tender)

    def create_question(self, tender, question):
        return self._create_tender_resource_item(tender, question, "questions")

    def create_bid(self, tender, bid):
        return self._create_tender_resource_item(tender, bid, "bids")

    ############################################################################
    #             GET ITEM API METHODS
    ############################################################################

    def _get_resource_item(self, url, headers={}):
        headers.update(self.headers)
        response_item = self.get(url, headers=headers)
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def get_tender(self, id):
        return self._get_resource_item(self.prefix_path + '/{}'.format(id))

    def _get_tender_resource_item(self, tender, item_id, items_name,
                                  access_token=""):
        if access_token:
            headers = {'X-Access-Token': access_token}
        else:
            headers = {'X-Access-Token': getattr(getattr(tender, 'access', ''), 'token', '')}
        return self._get_resource_item(
            self.prefix_path + '/{}/{}/{}'.format(tender.data.id, items_name, item_id),
            headers=headers
        )

    def get_question(self, tender, question_id):
        return self._get_tender_resource_item(tender, question_id, "questions")

    def get_bid(self, tender, bid_id, access_token):
        return self._get_tender_resource_item(tender, bid_id, "bids", access_token)

    ############################################################################
    #             PATCH ITEM API METHODS
    ############################################################################

    def _patch_resource_item(self, url, payload, headers={}):
        headers.update(self.headers)
        response_item = self.patch(
            url, headers=headers, payload=dumps(payload)
        )
        if response_item.status_int == 200:
            return munchify(loads(response_item.body_string()))
        raise InvalidResponse

    def _patch_tender_resource_item(self, tender, item_obj, items_name):
        return self._patch_resource_item(
            self.prefix_path + '/{}/{}/{}'.format(
                tender.data.id, items_name, item_obj.data.id
            ), item_obj, headers={'X-Access-Token': getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def patch_tender(self, tender):
        return self._patch_resource_item(
            self.prefix_path + '/{}'.format(tender["data"]["id"]), tender,
            headers={'X-Access-Token': getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def patch_question(self, tender, question):
        return self._patch_tender_resource_item(tender, question, "questions")

    def patch_bid(self, tender, bid):
        return self._patch_tender_resource_item(tender, bid, "bids")

    def patch_award(self, tender, award):
        return self._patch_tender_resource_item(tender, award, "awards")

    ############################################################################
    #             UPLOAD FILE API METHODS
    ############################################################################
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

    def upload_document(self, tender, file):
        return self._upload_resource_file(
            self.prefix_path + '/{}/documents'.format(tender.data.id),
            {"file": file},
            headers={'X-Access-Token': getattr(getattr(tender, 'access', ''), 'token', '')}
        )

    def update_document(self, tender, document_id, file):
        return self._upload_resource_file(
            self.prefix_path + '/{}/documents/{}'.format(
                tender.data.id, document_id
            ),
            {"file": file},
            headers={'X-Access-Token': getattr(getattr(tender, 'access', ''), 'token', '')},
            method='put'
        )
    ############################################################################
