import warnings

import zope.deferredimport


warnings.simplefilter("default")
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Import from openprocurement_client.utils instead.",
    verify_file='openprocurement_client.utils:verify_file'
)
zope.deferredimport.deprecated(
    "Import from openprocurement_client.templates instead.",
    APITemplateClient='openprocurement_client.templates:APITemplateClient'
)
zope.deferredimport.deprecated(
    "Import from openprocurement_client.clients instead.",
    APIBaseClient='openprocurement_client.clients:APIBaseClient'
)
