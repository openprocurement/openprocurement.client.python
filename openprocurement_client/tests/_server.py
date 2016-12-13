from bottle import request, response, redirect, static_file
from munch import munchify
from simplejson import dumps, load
from openprocurement_client.document_service_client \
    import DocumentServiceClient
from uuid import uuid4
import magic
import os

BASIS_URL = "http://localhost"
API_KEY = 'e9c3ccb8e8124f26941d5f9639a4ebc3'
API_VERSION = '0.10'
PORT = 20602
DS_PORT = 20603
HOST_URL = BASIS_URL + ':' + str(PORT)
DS_HOST_URL = BASIS_URL + ':' + str(DS_PORT)
AUTH_DS_FAKE = ['login_ds_fake', 'pass_ds_fake']
ROOT = os.path.dirname(__file__) + '/data/'
API_PATH = '/api/{0}/{1}'
TENDERS_PATH = API_PATH.format(API_VERSION, "tenders")
PLANS_PATH = API_PATH.format(API_VERSION, "plans")
CONTRACTS_PATH = API_PATH.format(API_VERSION, "contracts")
SPORE_PATH = API_PATH.format(API_VERSION, "spore")
DOWNLOAD_URL_EXTENSION = 'some_key_etc'


def setup_routing(app, routes=None):
    if routes is None:
        routes = ['spore']
    for route in routes:
        path, method, func = routes_dict[route]
        app.route(path, method, func)


def setup_routing_ds(app):
    for route in routes_dict_ds:
        path, method, func = routes_dict_ds[route]
        app.route(path, method, func)


def get_doc_title_from_request(req):
    if req.files.file:
        doc_title = req.files.file.filename
    else:
        doc_title = req.json['data']['title']
    return doc_title


### Base routes
#

def spore():
    response.set_cookie("SERVER_ID", ("a7afc9b1fc79e640f2487ba48243ca071c07a823d27"
                                      "8cf9b7adf0fae467a524747e3c6c6973262130fac2b"
                                      "96a11693fa8bd38623e4daee121f60b4301aef012c"))

def offset_error():
    response.status = 404
    setup_routing(request.app, routes=["tenders"])

def tenders_page_get():
    with open(ROOT + 'tenders.json') as json:
        tenders = load(json)
    return dumps(tenders)

### Tender operations
#

def tender_create():
    response.status = 201
    return request.json

def tender_page(tender_id):
    tender = tender_partition(tender_id)
    if not tender:
        return location_error("tender")
    return dumps(tender)

def tender_patch(tender_id):
    tender = tender_partition(tender_id)
    if not tender:
        return location_error("tender")
    tender.update(request.json['data'])
    return dumps({"data": tender})

### Subpage operations
#

def tender_subpage(tender_id, subpage_name):
    subpage = tender_partition(tender_id, subpage_name)
    return dumps({"data": subpage})

def tender_subpage_item_create(tender_id, subpage_name):
    response.status = 201
    if not tender_partition(tender_id, subpage_name):
        return location_error(subpage_name)
    return request.json

def tender_subpage_item(tender_id, subpage_name, subpage_id):
    subpage = tender_partition(tender_id, subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            return dumps({"data": unit})
    return location_error(subpage_name)

def tender_subpage_item_patch(tender_id, subpage_name, subpage_id):
    subpage = tender_partition(tender_id, subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            unit.update(request.json['data'])
            return dumps({"data": unit})
    return location_error(subpage_name)

def tender_subpage_item_delete(tender_id, subpage_name, subpage_id):
    subpage = tender_partition(tender_id, subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            response.status_int = 200
            return {}
    return location_error(subpage_name)

def tender_patch_credentials(tender_id):
    tender = tender_partition(tender_id)
    if not tender:
        return location_error("tender")
    tender['access'] = {'token': uuid4().hex}
    return tender

### Document and file operations
#

def tender_document_create(tender_id):
    from openprocurement_client.tests.tests import TEST_TENDER_KEYS
    response.status = 201
    document = tender_partition(tender_id, 'documents')[0]
    document.title = get_doc_title_from_request(request)
    document.id = TEST_TENDER_KEYS.new_document_id
    return dumps({"data": document})

def tender_subpage_document_create(tender_id, subpage_name, subpage_id, document_type):
    from openprocurement_client.tests.tests import TEST_TENDER_KEYS
    response.status = 201
    subpage = tender_partition(tender_id, subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            document= unit["documents"][0]
            document.title = get_doc_title_from_request(request)
            document.id = TEST_TENDER_KEYS.new_document_id
            return dumps({"data": document})
    return location_error(subpage_name)

def tender_subpage_document_update(tender_id, subpage_name, subpage_id, document_type, document_id):
    response.status = 200
    subpage = tender_partition(tender_id, subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            for document in unit[document_type]:
                if document['id'] == document_id:
                    document.title = get_doc_title_from_request(request)
                    return dumps({"data": document})
    return location_error(subpage_name)


def tender_subpage_document_patch(tender_id, subpage_name, subpage_id, document_type, document_id):
    response.status = 200
    subpage = tender_partition(tender_id, subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            for document in unit[document_type]:
                if document['id'] == document_id:
                    document.update(request.json['data'])
                    return dumps({"data": document})
    return location_error(subpage_name)

def get_file(filename):
    redirect("/download/" + filename, code=302)

def download_file(filename):
    return static_file(filename, root=ROOT, download=True)

####

def tender_partition(tender_id, part="tender"):
    try:
        with open(ROOT + tender_id + '.json') as json:
            tender = load(json)
            if part=="tender":
                return tender
            else:
                return munchify(tender['data'][part])
    except (KeyError, IOError):
        return []

def location_error(name):
    return dumps({"status": "error", "errors": [{"location": "url", "name": name + '_id', "description": "Not Found"}]})

### Plan operations
#

def plan_offset_error():
    response.status = 404
    setup_routing(request.app, routes=["plans"])

def plans_page_get():
    with open(ROOT + 'plans.json') as json:
        plans = load(json)
    return dumps(plans)

def plan_create():
    response.status = 201
    return request.json

def plan_page(plan_id):
    plan = plan_partition(plan_id)
    if not plan:
        return location_error("plan")
    return dumps(plan)

def plan_patch(plan_id):
    plan = plan_partition(plan_id)
    if not plan:
        return location_error("plan")
    plan.update(request.json['data'])
    return dumps({"data": plan})

def plan_partition(plan_id, part="plan"):
    try:
        with open(ROOT + 'plan_' + plan_id + '.json') as json:
            plan = load(json)
            if part=="plan":
                return plan
            else:
                return munchify(plan['data'][part])
    except (KeyError, IOError):
        return []

### Contract operations
#

def contract_offset_error():
    response.status = 404
    setup_routing(request.app, routes=["contracts"])

def contracts_page_get():
    with open(ROOT + 'contracts.json') as json:
        contracts = load(json)
    return dumps(contracts)

def contract_create():
    response.status = 201
    return request.json

def contract_page(contract_id):
    contract = contract_partition(contract_id)
    if not contract:
        return location_error("contract")
    return dumps(contract)

def contract_patch(contract_id):
    contract = contract_partition(contract_id)
    if not contract:
        return location_error("contract")
    contract.update(request.json['data'])
    return dumps({"data": contract})

def contract_document_create(contract_id):
    from openprocurement_client.tests.tests import TEST_CONTRACT_KEYS
    response.status = 201
    document = contract_partition(contract_id, 'documents')[0]
    document.title = get_doc_title_from_request(request)
    document.id = TEST_CONTRACT_KEYS.new_document_id
    return dumps({"data": document})

def contract_partition(contract_id, part="contract"):
    try:
        with open(ROOT + 'contract_' + contract_id + '.json') as json:
            contract = load(json)
            if part=="contract":
                return contract
            else:
                return munchify(contract['data'][part])
    except (KeyError, IOError):
        return []

#### Routes

routes_dict = {
        "spore": (SPORE_PATH, 'HEAD', spore),
        "offset_error": (TENDERS_PATH, 'GET', offset_error),
        "tenders": (TENDERS_PATH, 'GET', tenders_page_get),
        "tender_create": (TENDERS_PATH, 'POST', tender_create),
        "tender": (TENDERS_PATH + "/<tender_id>", 'GET', tender_page),
        "tender_patch": (TENDERS_PATH + "/<tender_id>", 'PATCH', tender_patch),
        "tender_document_create": (TENDERS_PATH + "/<tender_id>/documents", 'POST', tender_document_create),
        "tender_subpage": (TENDERS_PATH + "/<tender_id>/<subpage_name>", 'GET', tender_subpage),
        "tender_subpage_item_create": (TENDERS_PATH + "/<tender_id>/<subpage_name>", 'POST', tender_subpage_item_create),
        "tender_subpage_document_create": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>", 'POST', tender_subpage_document_create),
        "tender_subpage_document_update": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>/<document_id>", 'PUT', tender_subpage_document_update),
        "tender_subpage_document_patch": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>/<document_id>", 'PATCH', tender_subpage_document_patch),
        "tender_subpage_item": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>", 'GET', tender_subpage_item),
        "tender_subpage_item_patch": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>", 'PATCH', tender_subpage_item_patch),
        "tender_subpage_item_delete": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>", 'DELETE', tender_subpage_item_delete),
        "tender_patch_credentials": (TENDERS_PATH + "/<tender_id>/credentials", 'PATCH', tender_patch_credentials),
        "redirect": ('/redirect/<filename:path>', 'GET', get_file),
        "download": ('/download/<filename:path>', 'GET', download_file),
        "plans": (PLANS_PATH, 'GET', plans_page_get),
        "plan_create": (PLANS_PATH, 'POST', plan_create),
        "plan": (PLANS_PATH + "/<plan_id>", 'GET', plan_page),
        "plan_offset_error": (PLANS_PATH, 'GET', plan_offset_error),
        "contracts": (CONTRACTS_PATH, 'GET', contracts_page_get),
        "contract_create": (CONTRACTS_PATH, 'POST', contract_create),
        "contract_document_create": (CONTRACTS_PATH + "/<contract_id>/documents", 'POST', contract_document_create),
        "contract": (CONTRACTS_PATH + "/<contract_id>", 'GET', contract_page),
        "contract_offset_error": (CONTRACTS_PATH, 'GET', contract_offset_error)
        }


def file_info(file_):
    file_info_dict = {}
    file_info_dict['hash'] = 'md5:' + DocumentServiceClient._hashfile(file_)
    file_info_dict['mime'] \
        = magic.from_buffer(file_.read(1024), mime=True)
    file_.seek(0, 0)

    return file_info_dict

def register_document_upload_inside():
    req_json = request.json
    response.status = 201
    return dumps(
        {'upload_url': DS_HOST_URL + '/upload/' + DOWNLOAD_URL_EXTENSION,
         'data': {'url': DS_HOST_URL + '/get/' + DOWNLOAD_URL_EXTENSION,
                  'hash': req_json['data']['hash']}})


def document_upload_inside():
    file_ = request.files.file
    file_info_dict = file_info(file_.file)
    response.status = 200
    return dumps(
        {'get_url': DS_HOST_URL + '/get/' + DOWNLOAD_URL_EXTENSION,
         'data': {'url': DS_HOST_URL + '/get/' + DOWNLOAD_URL_EXTENSION,
                  'format': file_info_dict['mime'],
                  'hash': file_info_dict['hash'],
                  'title': file_.filename}}
    )


routes_dict_ds = {
    'register_document_upload': ('/register', 'POST', register_document_upload_inside),
    'document_upload':
        ('/upload/' + DOWNLOAD_URL_EXTENSION, 'POST', document_upload_inside)
}
