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
                 files=None,
                 headers=None):

        super(DocumentServiceClient, self)\
            .__init__(login_pass=auth_ds, headers=headers)

        self.prefix_path = host_url or self.host_url
        self.files = self.files_processing(files)

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
    def files_processing(cls, files=None):
        files_dict = {}
        if files:
            files_dict['hash'] = 'md5:' + cls.__hashfile(files)
            files_dict['mime'] \
                = magic.from_buffer(files.read(1024), mime=True)
            files.seek(0, 0)
            files_dict['file_payload'] = {'file': files}

        return files_dict

    def register_document_upload(self, hash_value, headers=None):
        response_item = self.request(
            'POST', path=self.prefix_path,
            json={'data': {'hash': hash_value}}, headers=headers
        )
        if response_item.status_code != 201:
            raise InvalidResponse(response_item)

        return munchify(loads(response_item.content))

    def document_upload(self, url, files, headers=None):
        response_item = self.request(
            'POST', url, headers=headers, files=files
        )

        if response_item.status_code != 200:
            raise InvalidResponse(response_item)

    def document_upload_registered(self, files, headers):

        self.files = self.files_processing(files)

        file_name = self.files['file_payload']['file'].name
        hash_value = self.files['hash']

        response_reg = self.register_document_upload(
            hash_value=hash_value,
            headers=headers
        )
        self.document_upload(
            url=response_reg.upload_url,
            files=self.files['file_payload'],
            headers=headers
        )

        return {'url': response_reg['data']['url'],
                'hash': hash_value,
                'title': file_name}
