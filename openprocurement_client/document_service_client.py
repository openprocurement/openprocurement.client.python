import hashlib
import magic

from .api_base_client import APITemplateClient
from .exceptions import InvalidResponse

from munch import munchify
from simplejson import dumps, loads


IGNORE_PARAMS = ('uri', 'path')


class DocumentServiceClient(APITemplateClient):
    """base class for API"""

    # header_auth = 'Basic YnJva2VyOmJyb2tlcg=='
    login = 'broker'
    passwd = 'broker'

    host_url = 'https://upload.docs-sandbox.openprocurement.org/register'

    def __init__(self,
                 api_version,
                 resource,
                 host_url=None,
                 files=None,
                 params=None):

        host_url_current = host_url or self.host_url
        super(DocumentServiceClient, self).__init__(
            host_url_current, api_version, resource,
            auth=self.auth(self.login, self.passwd), params=params
        )

        self.files = self.files_processing(files)

    @staticmethod
    def __hashfile(afile, hasher=hashlib.md5(), blocksize=65536):
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
        afile.seek(0, 0)
        return hasher.hexdigest()

    @classmethod
    def files_processing(cls, files=None):
        # files = {'file': (file_name, FileIO(file_path, 'rb'))}

        files_dict = {}
        if files:
            file_obj = files['file'][1]
            files_dict['md5'] = 'md5:' + cls.__hashfile(file_obj)
            files_dict['mime'] \
                = magic.from_buffer(file_obj.read(1024), mime=True)
            file_obj.seek(0, 0)
            files_dict['file_payload'] = files

        return files_dict

    def register_document_upload(self, payload, headers={}):
        response_item = self.request(
            'POST', path=self.host_url, json=payload, headers=headers
        )
        if response_item.status_code != 201:
            raise InvalidResponse(response_item)

        return munchify(loads(response_item.content))

    def document_upload(self, url, files=None, headers={}):
        file_current = files or self.files

        # file_payload = {'file': (file_name, FileIO(file_path, 'rb'))}
        file_payload = file_current['file_payload']
        response_item = self.request(
            'POST', url, headers=headers, files=file_payload
        )

        if response_item.status_code != 200:
            raise InvalidResponse(response_item)

        return munchify(loads(response_item.content))
