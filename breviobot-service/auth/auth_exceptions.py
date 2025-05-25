from core.exceptions import BrevioBotError

class AuthenticationError(BrevioBotError):
    """Raised when authentication fails"""
    pass

class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""
    pass

class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    pass
