from abc import ABC
from typing import Optional
from ..config.settings import Config

class BaseService(ABC):
    """Base class for all services."""
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
