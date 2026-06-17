import requests
import time
from typing import Generator, Any
from ..auth.base import BaseAuthenticator
from .base import ApiBase

class FabricApiClient(ApiBase):
    _LRO_ACTIVE = frozenset({"NotStarted", "Running", "InProgress"})

    def __init__(self, authenticator: BaseAuthenticator):
        super().__init__(authenticator)
        self._authenticator = authenticator

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._authenticator.acquire_token()}",
            "Content-Type": "application/json"
        }

    def call(self, method: str, url: str, **kwargs) -> Generator[Any, None, None]:
        """Entry point that handles LROs, Throttling, and Pagination."""
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())
        
        current_url = url
        current_method = method

        while True:
            response = requests.request(current_method, current_url, headers=headers, **kwargs)
            
            # 1. Handle Throttling (429)
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 5))
                time.sleep(wait_time)
                continue # Retry the same request

            # 2. Handle Long Running Operations (202)
            if response.status_code == 202:
                operation_url = response.headers.get("Location")
                if not operation_url:
                    raise Exception("LRO started but no Location header provided.")

                retry_after = int(response.headers.get("Retry-After", 5))
                current_url = self._handle_lro_operation(
                    operation_url, headers, retry_after
                )
                current_method = "GET"
                kwargs = {}
                continue

            # 3. Handle Success & Pagination
            if response.ok:
                yield from self._handle_pagination(response, headers)
                break
            else:
                response.raise_for_status()

    def _handle_lro_operation(
        self, operation_url: str, headers: dict, initial_retry_after: int
    ) -> str:
        """Poll operation URL until Succeeded or Failed; return the /result URL."""
        wait_time = initial_retry_after
        while True:
            time.sleep(wait_time)
            response = requests.get(operation_url, headers=headers)

            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 5))
                continue

            response.raise_for_status()
            data = response.json()
            status = data.get("status")

            if status in self._LRO_ACTIVE:
                wait_time = int(response.headers.get("Retry-After", 5))
                continue
            if status == "Failed":
                raise RuntimeError(f"LRO failed: {data.get('error')}")
            if status == "Succeeded":
                return f"{operation_url.rstrip('/')}/result"

            return operation_url

    def _handle_pagination(self, response: requests.Response, headers: dict) -> Generator[Any, None, None]:
        """Iterates through Fabric pages if continuation tokens exist."""
        data = response.json()
        
        # Fabric usually returns a list of items in a 'value' key
        yield data
        
        # MS Fabric uses 'continuationUri' or 'continuationToken'
        # If 'continuationUri' is present, we follow it.
        next_link = data.get("continuationUri")
        
        if next_link:
            yield from self.call("GET", next_link)