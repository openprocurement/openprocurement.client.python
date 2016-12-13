class ResourceError(Exception):
    """ default error class """

    status_code = None

    def __init__(self, response=None):
        self.message = getattr(response, 'text', 'Not described error yet.')
        self.status_code \
            = self.status_code or getattr(response, 'status_code', None)
        self.response = response

    def __str__(self):
        if self.message:
            return self.message
        try:
            return str(self.__dict__)
        except (NameError, ValueError, KeyError) as e:
            return 'Unprintable exception {}: {}'\
                .format(self.__class__.__name__, str(e))


class MethodNotAllowed(ResourceError):
    """
    A request method is not supported for the requested resource; for example,
    a GET request on a form which requires data to be presented via POST, or a
    PUT request on a read-only resource.
    """
    status_code = 405


class Conflict(ResourceError):
    """
    Indicates that the request could not be processed because of conflict in
    the request, such as an edit conflict between multiple simultaneous
    updates.
    """
    status_code = 409


class PreconditionFailed(ResourceError):
    """
    The server does not meet one of the preconditions that the requester put
    on the request.
    """
    status_code = 412


class UnprocessableEntity(ResourceError):
    """
    The request was well-formed but was unable to be followed due to
    semantic errors.
    """
    status_code = 422


class Locked(ResourceError):
    """
    The resource that is being accessed is locked
    """
    status_code = 423


class ResourceNotFound(ResourceError):
    """Exception raised when no resource was found at the given url.
    """
    status_code = 404


class ResourceGone(ResourceError):
    """
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.11
    """
    status_code = 410


class RequestFailed(ResourceError):
    """Exception raised when an unexpected HTTP error is received in response
    to a request.


    The request failed, meaning the remote HTTP server returned a code
    other than success, unauthorized, or NotFound.

    The exception message attempts to extract the error

    You can get the status code by e.status_code, or see anything about the
    response via e.response. For example, the entire result body (which is
    probably an HTML error page) is e.response.body.
    """


class Unauthorized(ResourceError):
    """Exception raised when an authorization is required to access to
    the resource specified.
    """
    status_code = 401


class Forbidden(ResourceError):
    """The request was a valid request, but the server is refusing to respond
    to it. The user might be logged in but does not have the necessary
    permissions for the resource.
    """
    status_code = 403


class InvalidResponse(ResourceError):
    """Exception raised when a response (usually response.status_code) doesn't
    match an expected one.
    """
    pass


class NoToken(ResourceError):
    pass


class IdNotFound(ResourceError):
    pass


http_exceptions_dict = {
    405: MethodNotAllowed,
    409: Conflict,
    412: PreconditionFailed,
    422: UnprocessableEntity,
    423: Locked,
    404: ResourceNotFound,
    410: ResourceGone,
    401: Unauthorized,
    403: Forbidden
}
