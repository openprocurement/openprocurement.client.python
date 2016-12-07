import hashlib
import magic

from .api_base_client import APITemplateClient
from .exceptions import InvalidResponse

from munch import munchify
from simplejson import dumps, loads


IGNORE_PARAMS = ('uri', 'path')


class DocumentServiceClient(APITemplateClient):
    """base class for API"""

    host_url = 'https://upload.docs-sandbox.openprocurement.org/register'

    def __init__(self,
                 host_url,
                 auth_ds,
                 file_=None,
                 headers=None):

        super(DocumentServiceClient, self)\
            .__init__(login_pass=auth_ds, headers=headers)

        self.prefix_path = host_url or self.host_url
        self.file_ = self.file_processing(file_)

    @staticmethod
    def __hashfile(afile, hasher=None, blocksize=65536):
        if hasher is None:
            hasher = hashlib.md5()
        afile.seek(0, 0)
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
        afile.seek(0, 0)
        return hasher.hexdigest()

    @classmethod
    def file_processing(cls, file_=None):
        files_dict = {}
        if file_:
            files_dict['hash'] = 'md5:' + cls.__hashfile(file_)
            files_dict['mime'] \
                = magic.from_buffer(file_.read(1024), mime=True)
            file_.seek(0, 0)
            files_dict['file_payload'] = {'file': file_}

        return files_dict

    def register_document_upload(self, hash_value, headers=None):
        response_item = self.request(
            'POST', path=self.prefix_path,
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

    def document_upload_registered(self, file_, headers):

        self.file_ = self.file_processing(file_)

        file_name = self.file_['file_payload']['file'].name
        hash_value = self.file_['hash']

        response_reg = self.register_document_upload(
            hash_value=hash_value,
            headers=headers
        )
        self._document_upload(
            url=response_reg.upload_url,
            file_=self.file_['file_payload'],
            headers=headers
        )

        return {'url': response_reg['data']['url'],
                'hash': hash_value,
                'title': file_name}
