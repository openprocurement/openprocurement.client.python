from restkit.errors import ResourceNotFound as BaseResourceNotFound

class ResourceNotFound(BaseResourceNotFound):
    pass

class InvalidResponse(Exception):
    pass


class NoToken(Exception):
    pass


class IdNotFound(Exception):
    pass
