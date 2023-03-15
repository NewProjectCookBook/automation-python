from __future__ import annotations
from typing import Any
import allure
from httpx import AsyncClient, Response, Cookies

from clients.api_client import Headers


class AsyncApiClient:

    def __init__(self, config: dict[str, Any], cookies: dict[str, str] | Cookies, timeout: int = 600,
                 verify: bool = False, cert: tuple[str, str] | None = None, follow_redirects: bool = True) -> None:
        self.verify = verify
        self.cookies = cookies
        self.timeout = timeout
        self.base_url = f'{config["protocol"]}{config["url"]}' if not verify \
            else f'{config["protocol_ssl"]}{config["url_ssl"]}'
        self.cert = cert
        self.follow_redirects = follow_redirects
        self.latest_request = None
        self.client = AsyncClient(verify=self.verify, timeout=self.timeout, cert=self.cert,
                                  follow_redirects=self.follow_redirects)

    @property
    def get_headers(self) -> Headers:
        return Headers.NONE_TYPE

    @property
    def get_cookies(self) -> dict[str, str]:
        return self.cookies

    # TODO: Add a hook for allure
    async def __aenter__(self) -> AsyncApiClient:
        return self

    async def get(self, path: str, status_code: int | None = None, params: dict | None = None,
                  headers: Headers | None = None) -> Response:
        self.latest_request = await self.client.get(url=f'{self.base_url}{path}', cookies=self.cookies, params=params,
                                                    headers=headers.value if headers else self.get_headers.value)
        self.check_status_code(status_code=status_code)
        return self.latest_request

    async def post(self, path: str, headers: Headers, params: dict | None = None,
                   files: dict[str, tuple] | list | None = None, data: Any = None, json: dict[str, Any] = None,
                   status_code: int | None = None) -> Response:
        self.latest_request = await self.client.post(
            url=f'{self.base_url}{path}', cookies=self.cookies, params=params,
            files=self._encode_data(files=files) if isinstance(files, dict) else files,
            data=data, json=json, headers=headers.value
        )
        self.check_status_code(status_code=status_code)
        return self.latest_request

    @staticmethod
    def _encode_data(files: dict[str, tuple]) -> dict[str, Any]:
        f = {}
        for k, v in files.items():
            if len(v) == 2:
                fn, fp = v
            elif len(v) == 3:
                fn, fp, ft = v
            else:
                fn, fp, ft, fh = v
            if fp:
                if isinstance(fp, str):
                    fdata = fp.encode()
                elif isinstance(fp, (bool, int)):
                    fdata = str(fp).encode()
                elif hasattr(fp, 'read'):
                    fdata = fp.read()
                if len(v) == 2:
                    f[k] = (fn, fdata)
                elif len(v) == 3:
                    f[k] = (fn, fdata, ft)
                else:
                    f[k] = (fn, fdata, ft, fh)
        return f

    def check_status_code(self, status_code: int | None) -> None:
        with allure.step('Checking the status of the request code'):
            if not status_code:
                assert self.latest_request, f'''An error occurred while executing the request. 
                                                Status code: {self.latest_request.status_code}. 
                                                Message: {self.latest_request.text}'''
            else:
                assert self.latest_request.status_code == status_code, \
                    f'''Invalid status code, expected: {status_code}. 
                        Received: {self.latest_request.status_code}. 
                        Message: {self.latest_request.text}'''

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.client.aclose()
