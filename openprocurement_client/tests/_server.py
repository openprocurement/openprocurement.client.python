from bottle import request, response, redirect, static_file
from munch import munchify
from simplejson import dumps, load
from openprocurement_client.document_service_client \
    import DocumentServiceClient
from openprocurement_client.tests.data_dict import TEST_TENDER_KEYS, \
    TEST_TENDER_KEYS_LIMITED, TEST_PLAN_KEYS, TEST_CONTRACT_KEYS
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
API_PATH = '/api/' + API_VERSION + '/{0}'
TENDERS_PATH = API_PATH.format('tenders')
PLANS_PATH = API_PATH.format('plans')
CONTRACTS_PATH = API_PATH.format('contracts')
SPORE_PATH = API_PATH.format('spore')
DOWNLOAD_URL_EXTENSION = 'some_key_etc'
PROCUR_ENTITY_DICT = \
    {'tender':   {'sublink': 'tenders',   'data': TEST_TENDER_KEYS},
     'contract': {'sublink': 'contracts', 'data': TEST_CONTRACT_KEYS},
     'plan':     {'sublink': 'plans',     'data': TEST_PLAN_KEYS}}


def procur_entity_filter(procur_entity_name):
    regexp = r'{}'.format(PROCUR_ENTITY_DICT[procur_entity_name]['sublink'])
    return regexp, lambda x: procur_entity_name, lambda x: None


def setup_routing(app, routes=None):
    if routes is None:
        routes = ['spore']
    else:
        app.router.add_filter('procur_entity_filter', procur_entity_filter)
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


def procurement_entity_create():
    response.status = 201
    return request.json


def procur_entity_page(procur_entity_name, procur_entity_id):
    procur_entity = procurement_entity_partition(procur_entity_id,
                                                 procur_entity_name)
    if not procur_entity:
        return location_error(procur_entity_name)
    return dumps(procur_entity)


def procur_entity_patch(procur_entity_name, procur_entity_id):
    procur_entity = procurement_entity_partition(procur_entity_id,
                                                 procur_entity_name)
    if not procur_entity:
        return location_error(procur_entity_name)
    procur_entity.update(request.json['data'])
    return dumps({'data': procur_entity})


### Subpage operations
#

def tender_subpage(tender_id, subpage_name):
    subpage = procurement_entity_partition(tender_id, part=subpage_name)
    return dumps({"data": subpage})

def tender_subpage_item_create(tender_id, subpage_name):
    response.status = 201
    return request.json

def procurement_entity_subpage_item_create(procurement_entity_id, subpage_name):
    response.status = 201
    return request.json

def tender_subpage_item(tender_id, subpage_name, subpage_id):
    subpage = procurement_entity_partition(tender_id, part=subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            return dumps({'data': unit})
    return location_error(subpage_name)

def object_subpage_item_patch(obj_id, subpage_name, subpage_id, procur_entity_name):
    subpage = procurement_entity_partition(obj_id, procur_entity_name, subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            unit.update(request.json['data'])
            return dumps({'data': unit})
    return location_error(subpage_name)

def tender_subpage_item_delete(tender_id, subpage_name, subpage_id):
    subpage = procurement_entity_partition(tender_id, part=subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            response.status_int = 200
            return {}
    return location_error(subpage_name)


def patch_credentials(procur_entity_name, procurement_entity_id):
    procur_entity = procurement_entity_partition(procurement_entity_id,
                                                 procur_entity_name)
    if not procur_entity:
        return location_error(
            PROCUR_ENTITY_DICT[procur_entity_name]['sublink'])
    procur_entity['access'] = \
        {'token': PROCUR_ENTITY_DICT[procur_entity_name]['data']['new_token']}
    return procur_entity

### Document and file operations
#

def tender_document_create(tender_id):
    response.status = 201
    document = procurement_entity_partition(tender_id, part='documents')[0]
    document.title = get_doc_title_from_request(request)
    document.id = TEST_TENDER_KEYS.new_document_id
    return dumps({"data": document})

def tender_subpage_document_create(tender_id, subpage_name, subpage_id, document_type):
    response.status = 201
    subpage = procurement_entity_partition(tender_id, part=subpage_name)
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
    subpage = procurement_entity_partition(tender_id, part=subpage_name)
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
    subpage = procurement_entity_partition(tender_id, part=subpage_name)
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


def procurement_entity_partition(entity_id, procur_entity_name='tender',
                                 part='all'):
    try:
        with open(ROOT + procur_entity_name + '_' + entity_id + '.json') \
                as json:
            obj = munchify(load(json))
            if part == 'all':
                return obj
            else:
                return munchify(obj['data'][part])
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


def contracts_page_get():
    with open(ROOT + 'contracts.json') as json:
        contracts = load(json)
    return dumps(contracts)

def contract_document_create(contract_id):
    response.status = 201
    document = procurement_entity_partition(contract_id,
                                            procur_entity_name='contract',
                                            part='documents')[0]
    document.title = get_doc_title_from_request(request)
    document.id = TEST_CONTRACT_KEYS.new_document_id
    return dumps({"data": document})


def contract_change_patch(contract_id, change_id):
    response.status = 200
    change = procurement_entity_partition(change_id,
                                          procur_entity_name='change')
    change.data.rationale = TEST_CONTRACT_KEYS.patch_change_rationale
    return dumps(change)

#### Routes


routes_dict = {
        "spore": (SPORE_PATH, 'HEAD', spore),
        "offset_error": (TENDERS_PATH, 'GET', offset_error),
        "tenders": (TENDERS_PATH, 'GET', tenders_page_get),
        "tender_create": (TENDERS_PATH, 'POST', procurement_entity_create),
        "tender": (API_PATH.format('<procur_entity_name:procur_entity_filter:tender>') + '/<procur_entity_id>', 'GET', procur_entity_page),
        "tender_patch": (API_PATH.format('<procur_entity_name:procur_entity_filter:tender>') + "/<procur_entity_id>", 'PATCH', procur_entity_patch),
        "tender_document_create": (TENDERS_PATH + "/<tender_id>/documents", 'POST', tender_document_create),
        "tender_subpage": (TENDERS_PATH + "/<tender_id>/<subpage_name>", 'GET', tender_subpage),
        "tender_subpage_item_create": (TENDERS_PATH + "/<procurement_entity_id>/<subpage_name>", 'POST', procurement_entity_subpage_item_create),
        "tender_subpage_document_create": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>", 'POST', tender_subpage_document_create),
        "tender_subpage_document_update": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>/<document_id>", 'PUT', tender_subpage_document_update),
        "tender_subpage_document_patch": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>/<document_id>", 'PATCH', tender_subpage_document_patch),
        "tender_subpage_item": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>", 'GET', tender_subpage_item),
        "tender_subpage_item_patch": (API_PATH.format('<procur_entity_name:procur_entity_filter:tender>') + '/<obj_id>/<subpage_name>/<subpage_id>', 'PATCH', object_subpage_item_patch),
        "tender_subpage_item_delete": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>", 'DELETE', tender_subpage_item_delete),
        "tender_patch_credentials": (API_PATH.format('<procur_entity_name:procur_entity_filter:tender>') + '/<procurement_entity_id>/credentials', 'PATCH', patch_credentials),
        "redirect": ('/redirect/<filename:path>', 'GET', get_file),
        "download": ('/download/<filename:path>', 'GET', download_file),
        "plans": (PLANS_PATH, 'GET', plans_page_get),
        "plan_create": (PLANS_PATH, 'POST', procurement_entity_create),
        "plan": (API_PATH.format('<procur_entity_name:procur_entity_filter:plan>') + '/<procur_entity_id>', 'GET', procur_entity_page),
        "plan_offset_error": (PLANS_PATH, 'GET', plan_offset_error),
        "contracts": (CONTRACTS_PATH, 'GET', contracts_page_get),
        "contract_create": (CONTRACTS_PATH, 'POST', procurement_entity_create),
        "contract_document_create": (CONTRACTS_PATH + "/<contract_id>/documents", 'POST', contract_document_create),
        "contract": (API_PATH.format('<procur_entity_name:procur_entity_filter:contract>') + '/<procur_entity_id>', 'GET', procur_entity_page),
        "contract_subpage_item_create": (CONTRACTS_PATH + "/<procurement_entity_id>/<subpage_name>", 'POST', procurement_entity_subpage_item_create),
        "contract_subpage_item_patch": (API_PATH.format('<procur_entity_name:procur_entity_filter:contract>') + '/<obj_id>/<subpage_name>/<subpage_id>', 'PATCH', object_subpage_item_patch),
        "contract_change_patch": (API_PATH.format('contracts') + '/<contract_id>/changes/<change_id>', 'PATCH', contract_change_patch),
        "contract_patch": (API_PATH.format('<procur_entity_name:procur_entity_filter:contract>') + "/<procur_entity_id>", 'PATCH', procur_entity_patch),
        "contract_patch_credentials": (API_PATH.format('<procur_entity_name:procur_entity_filter:contract>') + '/<procurement_entity_id>/credentials', 'PATCH', patch_credentials),
        }

# tender_subpage_item_patch

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
