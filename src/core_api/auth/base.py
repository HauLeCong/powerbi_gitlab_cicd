
from abc import ABC, abstractmethod

class BaseAuthenticator(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def acquire_token(self):
        pass