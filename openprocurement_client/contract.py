# -*- coding: utf-8 -*-
import warnings

import zope.deferredimport


warnings.simplefilter("default")
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Import from openprocurement_client.resources.contracts instead.",
    ContractingClient='openprocurement_client.resources.contracts:ContractingClient'
)
