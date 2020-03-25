# -*- coding: utf-8 -*-
from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import CATEGORIES, PROFILES, SUPPLIERS


class CategoriesClient(APIResourceClient):
    """ Client for eCatalogues categories """
    resource = CATEGORIES

    def get_category(self, category_id):
        return self.get_resource_item(category_id)

    def get_category_suppliers(self, category_id):
        return self.get_resource_item_subitem(category_id, SUPPLIERS)


class ProfilesClient(APIResourceClient):
    """ Client for eCatalogues profiles """
    resource = PROFILES

    def get_profile(self, profile_id):
        return self.get_resource_item(profile_id)


class ECataloguesClient(object):

    def __init__(self, *args, **kwargs):
        self.categories = CategoriesClient(*args, **kwargs)
        self.profiles = ProfilesClient(*args, **kwargs)
