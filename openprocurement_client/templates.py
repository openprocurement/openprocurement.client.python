# -*- coding: utf-8 -*-
import uuid
from .exceptions import RequestFailed, http_exceptions_dict
from requests import Session
from requests.auth import HTTPBasicAuth as BasicAuth


class APITemplateClient(object):
    """Base class template for API"""

    def __init__(self, login_pass=None, headers=None, user_agent=None):
        self.headers = headers or {}
        self.session = Session()
        if login_pass is not None:
            self.session.auth = BasicAuth(*login_pass)

        if user_agent is None:
            self.session.headers['User-Agent'] = 'op.client/{}'.format(uuid.uuid4().hex)
        else:
            self.session.headers['User-Agent'] = user_agent

    def request(self, method, path=None, payload=None, json=None, headers=None, params_dict=None, file_=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        if file_:
            _headers.pop('Content-Type', None)

        response = self.session.request(
            method, path, data=payload, json=json, headers=_headers, params=params_dict, files=file_
        )

        if response.status_code >= 400:
            raise http_exceptions_dict.get(response.status_code, RequestFailed)(response)

        return response
