class BrevioBotError(Exception):
    """Base exception for BrevioBot errors"""
    pass

class ModelError(BrevioBotError):
    """Raised when there's an error with the AI model"""
    pass

class ValidationError(BrevioBotError):
    """Raised when input validation fails"""
    pass

class RateLimitError(BrevioBotError):
    """Raised when rate limit is exceeded"""
    pass

class ConfigurationError(BrevioBotError):
    """Raised when there's a configuration error"""
    pass

class AuthenticationError(BrevioBotError):
    """Raised when authentication fails"""
    pass
