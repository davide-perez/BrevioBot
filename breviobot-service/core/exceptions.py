class ModelError(Exception):
    """Raised when there's an error with the AI model"""
    pass

class ValidationError(Exception):
    """Raised when input validation fails"""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass
