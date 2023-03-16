from __future__ import annotations
import allure
import requests
from requests import Response
from enum import Enum
from typing import Any, Callable


def timeout_logging(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to add requests when request fails due to timeout"""
    def logging(*args: object, **kwargs: dict[str, Any]) -> Response:
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout as e:
            with allure.step(f'[{e.request.method}] --> {e.request.url}'):
                req_text = f'''[{e.request.method}] --> {e.request.url} \n'
                           headers: {e.request.headers} \n body: {e.request.body if e.request.body else ""}'''
                allure.attach(req_text, 'request', allure.attachment_type.TEXT)
                raise requests.exceptions.Timeout(e)
    return logging


def allure_listener(response: Response, *args: Any, **kwargs: Any) -> None:
    """Function for logging requests and responses for ApiClient"""

    def formatter(resp: Response) -> tuple[str, str]:
        """Formatting information for logging"""
        req_data = f'[{resp.request.method}] --> {resp.url} \n' \
                   f' headers: {resp.headers}'
        if resp.request.method == 'POST':
            req_data += f'\n body: {resp.request.body}'
        req_message = req_data
        resp_message = f'status_code: {resp.status_code} \n {req_data} \n Content: \n {resp.text}'
        return req_message, resp_message

    with allure.step(f'[{response.request.method}] --> {response.url}'):
        req_text, resp_text = formatter(response)
        allure.attach(req_text, 'request', allure.attachment_type.TEXT)
        allure.attach(resp_text, 'response', allure.attachment_type.TEXT)


class ApiClient:

    def __init__(self, config: dict[str, Any], cookies: dict[str, str],
                 ssl: bool = False, base_url: str | None = None) -> None:
        self.base_url = base_url or \
                        (f'{config["protocol"]}{config["url"]}' if not ssl
                         else f'{config["protocol_ssl"]}{config["url_ssl"]}')
        self.cookies = cookies
        self.latest_request = None

    @property
    def post_headers(self) -> Headers:
        return Headers.JSON_TYPE

    @property
    def get_headers(self) -> Headers:
        return Headers.NONE_TYPE

    @property
    def get_cookies(self) -> dict[str, str]:
        return self.cookies

    @timeout_logging
    def get(self, path: str, headers: Headers | None = None, params: dict | None = None, time_out: int = 180,
            status_code: int | None = None, cert: tuple[str, str] | None = None,
            allow_redirects: bool = True) -> Response:
        self.latest_request = requests.get(url=f'{self.base_url}{path}', cookies=self.get_cookies,
                                           params=params, headers=headers.value if headers else self.get_headers.value,
                                           timeout=time_out, verify=False,
                                           hooks={'response': allure_listener}, cert=cert,
                                           allow_redirects=allow_redirects)
        self.check_status_code(status_code=status_code)
        return self.latest_request

    @timeout_logging
    def post(self, path: str, headers: Headers, params: dict | None = None,
             files: dict | list | None = None, data: Any = None, json: dict | None = None,
             status_code: int | None = None, time_out: int = 600, cert: tuple[str, str] | None = None,
             allow_redirects: bool = True) -> Response:
        self.latest_request = requests.post(url=f'{self.base_url}{path}', cookies=self.get_cookies,
                                            params=params, headers=headers.value, timeout=time_out,
                                            files=files, data=data, json=json, verify=False,
                                            allow_redirects=allow_redirects,
                                            hooks={'response': allure_listener}, cert=cert)
        self.check_status_code(status_code=status_code)
        return self.latest_request

    @timeout_logging
    def delete(self, path: str, headers: Headers, status_code: int | None = None, time_out: int = 180,
               cert: tuple[str, str] | None = None) -> Response:
        self.latest_request = requests.delete(url=f'{self.base_url}{path}', cookies=self.get_cookies,
                                              headers=headers.value, timeout=time_out,
                                              verify=False, hooks={'response': allure_listener}, cert=cert)
        self.check_status_code(status_code=status_code)
        return self.latest_request

    def check_status_code(self, status_code: int | None) -> None:
        with allure.step('Checking the status of the request code'):
            if not status_code:
                assert self.latest_request, f'''An error occurred while executing the request.
                                                Status code: {self.latest_request.status_code}.
                                                Message: {self.latest_request.text}.'''
            else:
                assert self.latest_request.status_code == status_code, f'''Wrong status code,
                                                                       expected: {status_code} , 
                                                                       received: {self.latest_request.status_code} , 
                                                                       message: {self.latest_request.text}'''


class Headers(Enum):
    NONE_TYPE = None
    JSON_TYPE = {'Content-Type': 'application/json'}
    XML_TYPE = {'X-Requested-With': 'XMLHttpRequest'}
