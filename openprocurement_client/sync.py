# -*- coding: utf-8 -*-
import warnings

import zope.deferredimport


warnings.simplefilter("default")
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Import from openprocurement_client.resources.sync instead.",
    ResourceFeeder='openprocurement_client.resources.sync:ResourceFeeder',
    get_resource_items='openprocurement_client.resources.sync:get_resource_items',
    get_tenders='openprocurement_client.resources.sync:get_tenders'
)
zope.deferredimport.deprecated(
    "Import from openprocurement_client.utils instead.",
    get_response='openprocurement_client.utils:get_response'
)