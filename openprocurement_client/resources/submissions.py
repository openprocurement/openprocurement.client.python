import logging

from openprocurement_client.clients import APIResourceClient
from openprocurement_client.constants import (DOCUMENTS, SUBMISSIONS)

LOGGER = logging.getLogger(__name__)


class SubmissionsClient(APIResourceClient):
    """Client for submissions"""

    resource = SUBMISSIONS


    def create_submission(self, submission):
        return self.create_resource_item(submission)

