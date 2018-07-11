import warnings

import zope.deferredimport


warnings.simplefilter("default")
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Import from openprocurement_client.resources.tenders instead.",
    TendersClient='openprocurement_client.resources.tenders:TendersClient',
    Client='openprocurement_client.resources.tenders:Client',
    TendersClientSync='openprocurement_client.resources.tenders:TendersClientSync'
)
zope.deferredimport.deprecated(
    "Import from openprocurement_client.resources.edr instead.",
    EDRClient='openprocurement_client.resources.edr:EDRClient'
)
