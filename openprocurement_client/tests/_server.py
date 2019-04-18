from bottle import request, response, redirect, static_file
from munch import munchify
from simplejson import dumps, load
from openprocurement_client.resources.document_service \
    import DocumentServiceClient
from openprocurement_client.tests.data_dict import (
    TEST_TENDER_KEYS,
    TEST_PLAN_KEYS,
    TEST_CONTRACT_KEYS,
    TEST_ASSET_KEYS,
    TEST_LOT_KEYS,
    TEST_AGREEMENT_KEYS
)
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
AGREEMENTS_PATH = API_PATH.format('agreements')
SPORE_PATH = API_PATH.format('spore')
DOWNLOAD_URL_EXTENSION = 'some_key_etc'
RESOURCE_DICT = {
    'tender': {'sublink': 'tenders', 'data': TEST_TENDER_KEYS},
    'contract': {'sublink': 'contracts', 'data': TEST_CONTRACT_KEYS},
    'plan': {'sublink': 'plans', 'data': TEST_PLAN_KEYS},
    'asset': {'sublink': 'assets', 'data': TEST_ASSET_KEYS},
    'lot': {'sublink': 'lots', 'data': TEST_LOT_KEYS},
    'agreement': {'sublink': 'agreements', 'data': TEST_AGREEMENT_KEYS},
}


def resource_filter(resource_name):
    regexp = r'{}'.format(RESOURCE_DICT[resource_name]['sublink'])
    return regexp, lambda x: resource_name, lambda x: None


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


# Base routes


def spore():
    response.set_cookie(
        "SERVER_ID",
        ("a7afc9b1fc79e640f2487ba48243ca071c07a823d278cf9b7adf0fae467a524747"
         "e3c6c6973262130fac2b96a11693fa8bd38623e4daee121f60b4301aef012c"))


def offset_error(resource_name):
    response.status = 404
    setup_routing(request.app,
                  routes=[RESOURCE_DICT[resource_name]['sublink']])


def resource_page_get(resource_name):
    with open(ROOT + '{}.json'.format(
            RESOURCE_DICT[resource_name]['sublink'])) as json:
        resources = load(json)
    return dumps(resources)


# Tender operations

def resource_create():
    response.status = 201
    return request.json


def resource_page(resource_name, resource_id):
    resource = resource_partition(resource_id, resource_name)
    if not resource:
        return location_error(resource_name)
    return dumps(resource)


def resource_patch(resource_name, resource_id):
    resource = resource_partition(resource_id, resource_name)
    if not resource:
        return location_error(resource_name)
    resource['data'].update(request.json['data'])
    return dumps({'data': resource['data']})


# Subpage operations

def tender_subpage(tender_id, subpage_name):
    subpage = resource_partition(tender_id, part=subpage_name)
    return dumps({'data': subpage})


def tender_award_documents(tender_id, award_id):
    tender = resource_partition(tender_id)
    for award in tender['data']['awards']:
        if award['id'] == award_id:
            return dumps({'data': award['documents']})
    return location_error(award_id)


def tender_qualification_documents(tender_id, qualification_id):
    tender = resource_partition(tender_id)
    for qualification in tender['data']['qualifications']:
        if qualification['id'] == qualification_id:
            return dumps({'data': qualification['documents']})
    return location_error(qualification_id)


def tender_subpage_item_create(tender_id, subpage_name):
    response.status = 201
    return request.json


def resource_subpage_item_create(resource_id, subpage_name):
    response.status = 201
    return request.json


def tender_subpage_item(tender_id, subpage_name, subpage_id):
    subpage = resource_partition(tender_id, part=subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            return dumps({'data': unit})
    return location_error(subpage_name)


def object_subpage_item_patch(obj_id, subpage_name, subpage_id, resource_name):
    subpage = resource_partition(obj_id, resource_name, subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            unit.update(request.json['data'])
            return dumps({'data': unit})
    return location_error(subpage_name)


def tender_subpage_item_delete(tender_id, subpage_name, subpage_id):
    subpage = resource_partition(tender_id, part=subpage_name)
    for unit in subpage:
        if unit.id == subpage_id:
            response.status_int = 200
            return {}
    return location_error(subpage_name)


def patch_credentials(resource_name, resource_id):
    resource = resource_partition(resource_id, resource_name)
    if not resource:
        return location_error(RESOURCE_DICT[resource_name]['sublink'])
    resource['access'] = \
        {'token': RESOURCE_DICT[resource_name]['data']['new_token']}
    return resource

# Document and file operations


def tender_document_create(tender_id):
    response.status = 201
    document = resource_partition(tender_id, part='documents')[0]
    document.title = get_doc_title_from_request(request)
    document.id = TEST_TENDER_KEYS.new_document_id
    return dumps({"data": document})

def tender_document_update(tender_id, document_id):
    response.status = 200
    document = resource_partition(tender_id, part='documents')[0]
    document.title = get_doc_title_from_request(request)
    return dumps({"data": document})

def tender_subpage_document_create(tender_id, subpage_name, subpage_id,
                                   document_type):
    response.status = 201
    subpage = resource_partition(tender_id, part=subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            document = unit["documents"][0]
            document.title = get_doc_title_from_request(request)
            document.id = TEST_TENDER_KEYS.new_document_id
            return dumps({"data": document})
    return location_error(subpage_name)


def tender_subpage_document_update(tender_id, subpage_name, subpage_id,
                                   document_type, document_id):
    response.status = 200
    subpage = resource_partition(tender_id, part=subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            for document in unit[document_type]:
                if document['id'] == document_id:
                    document.title = get_doc_title_from_request(request)
                    return dumps({"data": document})
    return location_error(subpage_name)


def tender_subpage_document_patch(tender_id, subpage_name, subpage_id,
                                  document_type, document_id):
    response.status = 200
    subpage = resource_partition(tender_id, part=subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            for document in unit[document_type]:
                if document['id'] == document_id:
                    document.update(request.json['data'])
                    return dumps({"data": document})
    return location_error(subpage_name)

def tender_subpage_object_patch(tender_id, subpage_name, subpage_id, object_type, object_id):
    response.status = 200
    subpage = resource_partition(tender_id, part=subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            for obj in unit[object_type]:
                if obj['id'] == object_id:
                    obj.update(request.json['data'])
                    return dumps({"data": obj})
    return location_error(subpage_name)

def get_file(filename):
    redirect("/download/" + filename, code=302)


def download_file(filename):
    return static_file(filename, root=ROOT, download=True)


def resource_partition(resource_id, resource_name='tender', part='all'):
    try:
        with open(ROOT + resource_name + '_' + resource_id + '.json') \
                as json:
            obj = munchify(load(json))
            if part == 'all':
                return obj
            else:
                return munchify(obj['data'][part])
    except (KeyError, IOError):
        return []


def location_error(name):
    return dumps(
        {
            "status": "error",
            "errors": [
                {
                    "location": "url",
                    "name": name + '_id',
                    "description": "Not Found"
                }
            ]
        }
    )

# Plan operations


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
            if part == "plan":
                return plan
            else:
                return munchify(plan['data'][part])
    except (KeyError, IOError):
        return []

# Contract operations


def contract_document_create(contract_id):
    response.status = 201
    document = resource_partition(contract_id,
                                  resource_name='contract',
                                  part='documents')[0]
    document.title = get_doc_title_from_request(request)
    document.id = TEST_CONTRACT_KEYS.new_document_id
    return dumps({"data": document})

def contract_change_patch(contract_id, change_id):
    response.status = 200
    change = resource_partition(change_id, resource_name='change')
    change.data.rationale = TEST_CONTRACT_KEYS.patch_change_rationale
    return dumps(change)

def agreement_change_patch(agreement_id, change_id):
    response.status = 200
    change = resource_partition(change_id, resource_name='change')
    change.update(request.json['data'])
    return dumps({'data': change})

def agreement_document_patch(agreement_id, document_id):
    response.status = 200
    document = resource_partition(agreement_id, resource_name='agreement', part='documents')[0]
    document.update(request.json['data'])
    return dumps({'data': document})

def contract_patch_milestone(contract_id, milestone_id):
    response.status = 200
    milestone = resource_partition(milestone_id, resource_name='milestone')
    milestone.update(request.json['data'])
    return dumps({'data': milestone})

# Routes


routes_dict = {
    "spore": (SPORE_PATH, 'HEAD', spore),
    "offset_error": (API_PATH.format('<resource_name:resource_filter:tender>'),
                     'GET', offset_error),
    "tenders": (API_PATH.format('<resource_name:resource_filter:tender>'),
                'GET', resource_page_get),
    "tenders_head": (TENDERS_PATH, 'HEAD', spore),
    "tender_create": (TENDERS_PATH, 'POST', resource_create),
    "tender": (API_PATH.format(
        '<resource_name:resource_filter:tender>') + '/<resource_id>',
        'GET', resource_page),
    "tender_patch": (API_PATH.format('<resource_name:resource_filter:tender>') + "/<resource_id>", 'PATCH', resource_patch),
    "tender_document_create": (TENDERS_PATH + "/<tender_id>/documents", 'POST', tender_document_create),
    "tender_document_update": (TENDERS_PATH + "/<tender_id>/documents/<document_id>", 'PUT', tender_document_update),
    "tender_subpage": (TENDERS_PATH + "/<tender_id>/<subpage_name>", 'GET', tender_subpage),
    "tender_subpage_item_create": (TENDERS_PATH + "/<resource_id>/<subpage_name>", 'POST', resource_subpage_item_create),
    "tender_award_documents": (TENDERS_PATH + "/<tender_id>/awards/<award_id>/documents", 'GET', tender_award_documents),
    "tender_qualification_documents": (TENDERS_PATH + "/<tender_id>/qualifications/<qualification_id>/documents", 'GET', tender_qualification_documents),
    "tender_subpage_document_create": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>", 'POST', tender_subpage_document_create),
    "tender_subpage_document_update": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>/<document_id>", 'PUT', tender_subpage_document_update),
    "tender_subpage_document_patch": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<document_type>/<document_id>", 'PATCH', tender_subpage_document_patch),
    "tender_subpage_item": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>", 'GET', tender_subpage_item),
    "tender_subpage_item_patch": (API_PATH.format('<resource_name:resource_filter:tender>') + '/<obj_id>/<subpage_name>/<subpage_id>', 'PATCH', object_subpage_item_patch),
    "tender_subpage_item_delete": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>", 'DELETE', tender_subpage_item_delete),
    "tender_subpage_object_patch": (TENDERS_PATH + "/<tender_id>/<subpage_name>/<subpage_id>/<object_type>/<object_id>", 'PATCH', tender_subpage_object_patch),
    "tender_patch_credentials": (API_PATH.format('<resource_name:resource_filter:tender>') + '/<resource_id>/credentials', 'PATCH', patch_credentials),
    "redirect": ('/redirect/<filename:path>', 'GET', get_file),
    "download": ('/download/<filename:path>', 'GET', download_file),
    "plans": (API_PATH.format('<resource_name:resource_filter:plan>'), 'GET', resource_page_get),
    "plans_head": (API_PATH.format('plans'), 'HEAD', spore),
    "plan_create": (PLANS_PATH, 'POST', resource_create),
    "plan_patch": (API_PATH.format('<resource_name:resource_filter:plan>') + "/<resource_id>", 'PATCH', resource_patch),
    "plan": (API_PATH.format('<resource_name:resource_filter:plan>') + '/<resource_id>', 'GET', resource_page),
    "plan_offset_error": (API_PATH.format('<resource_name:resource_filter:plan>'), 'GET', offset_error),
    "contracts": (API_PATH.format('<resource_name:resource_filter:contract>'), 'GET', resource_page_get),
    "contracts_head": (CONTRACTS_PATH, 'HEAD', spore),
    "contract_create": (CONTRACTS_PATH, 'POST', resource_create),
    "contract_document_create": (CONTRACTS_PATH + "/<contract_id>/documents", 'POST', contract_document_create),
    "contract": (API_PATH.format('<resource_name:resource_filter:contract>') + '/<resource_id>', 'GET', resource_page),
    "contract_subpage_item_create": (CONTRACTS_PATH + "/<resource_id>/<subpage_name>", 'POST', resource_subpage_item_create),
    "contract_subpage_item_patch": (API_PATH.format('<resource_name:resource_filter:contract>') + '/<obj_id>/<subpage_name>/<subpage_id>', 'PATCH', object_subpage_item_patch),
    "contract_change_patch": (API_PATH.format('contracts') + '/<contract_id>/changes/<change_id>', 'PATCH', contract_change_patch),
    "contract_patch": (API_PATH.format('<resource_name:resource_filter:contract>') + "/<resource_id>", 'PATCH', resource_patch),
    "contract_patch_credentials": (API_PATH.format('<resource_name:resource_filter:contract>') + '/<resource_id>/credentials', 'PATCH', patch_credentials),
    "contract_patch_milestone": (API_PATH.format('contracts') + '/<contract_id>/milestones/<milestone_id>', 'PATCH', contract_patch_milestone),
    "assets": (API_PATH.format('<resource_name:resource_filter:asset>'), 'GET', resource_page_get),
    "assets_head": (API_PATH.format('assets'), 'HEAD', spore),
    "asset": (API_PATH.format('<resource_name:resource_filter:asset>') + '/<resource_id>', 'GET', resource_page),
    "asset_patch": (API_PATH.format('<resource_name:resource_filter:asset>') + "/<resource_id>", 'PATCH', resource_patch),
    "lots": (API_PATH.format('<resource_name:resource_filter:lot>'), 'GET', resource_page_get),
    "lots_head": (API_PATH.format('lots'), 'HEAD', spore),
    "lot": (API_PATH.format('<resource_name:resource_filter:lot>') + '/<resource_id>', 'GET', resource_page),
    "lot_patch": (API_PATH.format('<resource_name:resource_filter:lot>') + "/<resource_id>", 'PATCH', resource_patch),
    "agreement": (API_PATH.format('<resource_name:resource_filter:agreement>') + '/<resource_id>', 'GET', resource_page),
    "agreements": (API_PATH.format('<resource_name:resource_filter:agreement>'), 'GET', resource_page_get),
    "agreements_head": (API_PATH.format('agreements'), 'HEAD', spore),
    "agreement_patch": (API_PATH.format('<resource_name:resource_filter:agreement>') + "/<resource_id>", 'PATCH', resource_patch),
    "agreement_subpage_item_create": (AGREEMENTS_PATH + "/<resource_id>/<subpage_name>", 'POST', resource_subpage_item_create),
    "agreement_change_patch": (API_PATH.format('agreements') + '/<agreement_id>/changes/<change_id>', 'PATCH', agreement_change_patch),
    "agreement_document_patch": (API_PATH.format('agreements') + '/<agreement_id>/documents/<document_id>', 'PATCH', agreement_document_patch),
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
