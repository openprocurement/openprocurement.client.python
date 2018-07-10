# -*- coding: utf-8 -*-
import warnings

import zope.deferredimport


warnings.simplefilter("default")
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Import from openprocurement_client.resources.plans instead",
    PlansClient='openprocurement_client.resources.plans:PlansClient'
)
