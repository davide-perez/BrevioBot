class ModelError(Exception):
    """Raised when there's an error with the AI model"""
    pass

class ValidationError(Exception):
    """Raised when input validation fails"""
    pass

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

class ConfigurationError(Exception):
    """Raised when there's a configuration error"""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class TokenExpiredError(Exception):
    """Raised when JWT token has expired"""
    pass

class InvalidTokenError(Exception):
    """Raised when JWT token is invalid"""
    pass

class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid"""
    pass
