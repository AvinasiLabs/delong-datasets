class AuthError(Exception):
    pass


class NotFoundError(Exception):
    pass


class RateLimitError(Exception):
    pass


class RemoteServerError(Exception):
    pass


class NetworkError(Exception):
    pass


class ParseError(Exception):
    pass


class PolicyViolationError(Exception):
    pass


