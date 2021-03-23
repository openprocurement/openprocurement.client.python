import hashlib
from openprocurement_client.templates import APITemplateClient
from openprocurement_client.exceptions import InvalidResponse

from openprocurement_client.compatibility_utils import munchify_factory

from simplejson import loads


munchify = munchify_factory()
IGNORE_PARAMS = ('uri', 'path')


class DocumentServiceClient(APITemplateClient):
    """class for work with Document Service"""

    host_url = 'https://upload-docs-staging.prozorro.gov.ua'
    url_register_part = 'register'
    url_upload_part = 'upload'

    def __init__(self,
                 host_url,
                 auth_ds,
                 headers=None):

        super(DocumentServiceClient, self)\
            .__init__(login_pass=auth_ds, headers=headers)

        self.host_url = host_url or self.host_url
        self.host_url_register = \
            '/'.join((self.host_url, self.url_register_part))
        self.host_url_upload = '/'.join((self.host_url, self.url_upload_part))

    @staticmethod
    def _hashfile(file_, hasher=None, blocksize=65536):
        if hasher is None:
            hasher = hashlib.md5()
        file_.seek(0, 0)
        buf = file_.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file_.read(blocksize)
        file_.seek(0, 0)
        return hasher.hexdigest()

    def register_document_upload(self, hash_value, headers=None):
        response_item = self.request(
            'POST', path=self.host_url_register,
            json={'data': {'hash': hash_value}}, headers=headers
        )
        if response_item.status_code != 201:
            raise InvalidResponse(response_item)

        return munchify(loads(response_item.content))

    def _document_upload(self, url, file_, headers=None):
        response_item = self.request(
            'POST', url, headers=headers, file_=file_
        )

        if response_item.status_code != 200:
            raise InvalidResponse(response_item)

        return loads(response_item.text)

    def document_upload_registered(self, file_, headers):

        file_hash = 'md5:' + self._hashfile(file_)

        response = self.register_document_upload(
            hash_value=file_hash,
            headers=headers
        )
        return self._document_upload(
            url=response.upload_url,
            file_={'file': file_},
            headers=headers
        )

    def document_upload_not_registered(self, file_, headers):

        return self._document_upload(
            url=self.host_url_upload,
            file_={'file': file_},
            headers=headers
        )
