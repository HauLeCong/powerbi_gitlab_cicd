from abc import ABC, abstractmethod
from ..auth.base import BaseAuthenticator

class ApiBase(ABC):

    def __init__(self, authenticator: BaseAuthenticator):
        self.authenticator = authenticator
        
    @abstractmethod
    def call(self):
        "Perform generic api request"

    # @abstractmethod
    # def handle_response(self, response):
    #     "Handle error"


    