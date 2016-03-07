from bottle import request, response, redirect, static_file
from munch import munchify
from simplejson import dumps, load
import os


ROOT = os.path.dirname(__file__) + '/data/'

API_PATH = '/api/{0}/{1}'
TENDERS_PATH = API_PATH.format('0.10', "tenders")
SPORE_PATH = API_PATH.format('0.10', "spore")

def setup_routing(app, routs=None):
    if routs is None:
        routs = ['spore']
    routs = routs
    for route in routs:
        path, method, func = routs_dict[route]
        app.route(path, method, func)


### Base routes
#

def spore():
    response.set_cookie("SERVER_ID", ("a7afc9b1fc79e640f2487ba48243ca071c07a823d27"
                                      "8cf9b7adf0fae467a524747e3c6c6973262130fac2b"
                                      "96a11693fa8bd38623e4daee121f60b4301aef012c"))

def offset_error():
    response.status = 404
    setup_routing(request.app, routs=["tenders"])

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


### Document and file operations
#

def tender_document_create(tender_id):
    response.status = 201
    document = tender_partition(tender_id, 'documents')[0]
    document.title = request.files.file.filename
    document.id = '12345678123456781234567812345678'
    return dumps({"data": document})

def tender_subpage_document_create(tender_id, subpage_name, subpage_id, document_type):
    response.status = 201
    subpage = tender_partition(tender_id, subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            document= unit["documents"][0]
            document.title = request.files.file.filename
            document.id = '12345678123456781234567812345678'
            return dumps({"data": document})
    return location_error(subpage_name)

def tender_subpage_document_update(tender_id, subpage_name, subpage_id, document_type, document_id):
    response.status = 201
    subpage = tender_partition(tender_id, subpage_name)
    if not subpage:
        return location_error("tender")
    for unit in subpage:
        if unit['id'] == subpage_id:
            for document in unit[document_type]:
                if document['id'] == document_id:
                    document.title = request.files.file.filename
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

#### Routs

routs_dict = {
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
        "redirect": ('/redirect/<filename:path>', 'GET', get_file),
        "download": ('/download/<filename:path>', 'GET', download_file),
        }
