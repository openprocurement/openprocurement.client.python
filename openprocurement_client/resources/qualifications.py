import logging

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import (QUALIFICATIONS)

LOGGER = logging.getLogger(__name__)


class QualificationClient(APIResourceClient):
    """Client for qualification"""

    resource = QUALIFICATIONS

    def get_qualification(self, qualification_id):
        return self.get_resource_item(qualification_id)

    def patch_qualification(self, qualification_id, patch_data={}, access_token=None):
        return self.patch_resource_item(qualification_id, patch_data, access_token=access_token)

    def upload_qualification_document(self, file, qualification_id, use_ds_client=True,
                              doc_registration=True, access_token=None):
        return self.upload_document(file, qualification_id,
                                    use_ds_client=use_ds_client,
                                    doc_registration=doc_registration,
                                    access_token=access_token)