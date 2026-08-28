# Copyright 2025-     Tatu Aalto
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any
from unittest.mock import Mock

import pytest
from requests.structures import CaseInsensitiveDict
from schemathesis.config._output import SanitizationConfig
from schemathesis.core.transport import decode_lossy

from src.SchemathesisLibrary import SchemathesisLibrary

SECRET = "Basic am91bHU6cHVra2k="
FILTERED = "[Filtered]"


def _case(*, enabled: bool = True) -> Mock:
    case = Mock()
    case.headers = CaseInsensitiveDict({"Authorization": SECRET, "User-Agent": "schemathesis"})
    case.cookies = {"session": "s3cr3t", "theme": "dark"}
    case.body = {"password": "hunter2", "name": "joulu"}
    case.path_parameters = {"userid": 42}
    case.operation.schema.config.output.sanitization = SanitizationConfig(enabled=enabled)
    return case


def _response(
    *,
    body: object = None,
    request_headers: "dict[str, str]|None" = None,
    headers: "dict[str, list[str]]|None" = None,
    content: bytes = b"{}",
    encoding: str = "utf-8",
) -> Mock:
    response = Mock()
    response.request.method = "POST"
    response.request.url = "http://127.0.0.1/login"
    response.request.headers = CaseInsensitiveDict(
        request_headers if request_headers is not None else {"Content-Type": "application/json"}
    )
    response.request.body = body
    response.status_code = 200
    response.headers = headers if headers is not None else {"content-type": ["application/json"]}
    response.content = content
    response.encoding = encoding
    response.text_lossy = lambda: decode_lossy(content, encoding)
    return response


@pytest.fixture
def library() -> SchemathesisLibrary:
    return SchemathesisLibrary(url="http://127.0.0.1/openapi.json")


def test_log_case_does_not_leak_credentials(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    case = _case()

    library._log_case(case)

    assert len(logged) == 1
    assert SECRET not in logged[0]
    assert "s3cr3t" not in logged[0]
    assert "hunter2" not in logged[0]
    assert FILTERED in logged[0]


def test_log_case_leaves_the_case_untouched(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    """Sanitization must never mutate the case, or the real request loses its credentials."""
    monkeypatch.setattr(library, "info", lambda message: None)
    case = _case()

    library._log_case(case)

    assert case.headers["Authorization"] == SECRET
    assert case.cookies["session"] == "s3cr3t"
    assert case.body["password"] == "hunter2"


def test_log_case_keeps_values_that_are_not_sensitive(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_case(_case())

    assert "schemathesis" in logged[0]
    assert "dark" in logged[0]
    assert "'userid': 42" in logged[0]


def test_log_case_honours_disabled_sanitization(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_case(_case(enabled=False))

    assert SECRET in logged[0]
    assert FILTERED not in logged[0]


def test_log_case_prefers_given_headers(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    case = _case()

    library._log_case(case, {"Authorization": "Bearer token", "X-Trace": "abc"})

    assert "Bearer token" not in logged[0]
    assert FILTERED in logged[0]
    assert "abc" in logged[0]


def test_log_request_does_not_leak_credentials(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    case = _case()
    response = Mock()
    response.request.method = "GET"
    response.request.url = "http://127.0.0.1/user/1?api_key=s3cr3t"
    response.request.headers = CaseInsensitiveDict({"Authorization": SECRET})
    response.request.body = None

    library._log_request(case, response)

    assert len(logged) == 1
    assert SECRET not in logged[0]
    assert "s3cr3t" not in logged[0]
    assert FILTERED in logged[0]
    assert response.request.headers["Authorization"] == SECRET


def test_log_request_sanitizes_a_json_body(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    """The body on the wire is bytes, so it has to be parsed before it can be sanitized."""
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    case = _case()
    response = _response(body=b'{"password": "hunter2", "name": "joulu"}')

    library._log_request(case, response)

    assert "hunter2" not in logged[0]
    assert FILTERED in logged[0]
    assert "joulu" in logged[0]


def test_log_request_leaves_a_body_without_secrets_as_it_is(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    """Untouched bodies keep the exact form they were sent in."""
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_request(_case(), _response(body=b'{"name": "joulu", "price": 1}'))

    assert 'body: b\'{"name": "joulu", "price": 1}\'' in logged[0]


def test_log_request_leaves_a_body_that_is_not_json_as_it_is(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_request(_case(), _response(body=b"<xml>not json</xml>"))

    assert "<xml>not json</xml>" in logged[0]


def test_log_request_honours_disabled_sanitization_for_the_body(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_request(_case(enabled=False), _response(body=b'{"password": "hunter2"}'))

    assert "hunter2" in logged[0]


def test_log_case_is_logged_at_info_level(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    """The case is the only record of what was sent when validation fails before the request is logged."""
    debugged: list[str] = []
    monkeypatch.setattr(library, "debug", debugged.append)
    monkeypatch.setattr(library, "info", lambda message: None)

    library._log_case(_case())

    assert debugged == []


def test_log_request_is_logged_at_info_level(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    debugged: list[str] = []
    monkeypatch.setattr(library, "debug", debugged.append)
    monkeypatch.setattr(library, "info", lambda message: None)

    library._log_request(_case(), _response())

    assert debugged == []


def test_log_request_names_the_cookies_that_were_sent(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    """The ``Cookie`` header is filtered whole, so the cookies in it are logged one by one."""
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    response = _response(request_headers={"Cookie": "session=s3cr3t; theme=dark"})

    library._log_request(_case(), response)

    assert "cookies: {'session': '[Filtered]', 'theme': 'dark'}" in logged[0]
    assert "s3cr3t" not in logged[0]


def test_log_request_logs_no_cookies_when_none_were_sent(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_request(_case(), _response())

    assert "cookies: {}" in logged[0]


def test_log_request_survives_a_cookie_header_it_can_not_parse(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    """Generated cases carry values no cookie parser accepts, and logging must not be what fails the test."""
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_request(_case(), _response(request_headers={"Cookie": "=;;; not a cookie"}))

    assert "cookies: {}" in logged[0]


def test_log_response_logs_status_headers_and_body(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    debugged: list[str] = []
    monkeypatch.setattr(library, "debug", debugged.append)

    library._log_response(_case(), _response(content=b'{"message": "hello"}'))

    assert len(logged) == 1
    assert debugged == []
    assert "200" in logged[0]
    assert "'content-type': ['application/json']" in logged[0]
    assert 'body: \'{"message": "hello"}\'' in logged[0]


def test_log_response_names_the_cookies_that_were_set(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    response = _response(headers={"set-cookie": ["session=s3cr3t; Path=/", "theme=dark"]})

    library._log_response(_case(), response)

    assert "cookies: {'session': '[Filtered]', 'theme': 'dark'}" in logged[0]
    assert "s3cr3t" not in logged[0]


def test_log_response_does_not_leak_a_credential_in_a_header(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    headers = {"authorization": [SECRET]}

    library._log_response(_case(), _response(headers=headers))

    assert SECRET not in logged[0]
    assert FILTERED in logged[0]
    assert headers["authorization"] == [SECRET]


def test_log_response_honours_disabled_sanitization(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_response(_case(enabled=False), _response(headers={"authorization": [SECRET]}))

    assert SECRET in logged[0]
    assert FILTERED not in logged[0]


def test_log_response_survives_a_body_that_is_not_text(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    """A binary body must not raise after the checks already passed."""
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_response(_case(), _response(content=b"\xff\xfe binary"))

    assert len(logged) == 1
    assert "binary" in logged[0]


def test_log_request_keeps_a_cookie_http_cookies_would_drop(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    """``http.cookies`` stops at a segment it can not read and loses every cookie after it."""
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    response = _response(request_headers={"Cookie": 'a=1; bad="x; theme=dark'})

    library._log_request(_case(), response)

    assert "'theme': 'dark'" in logged[0]
    assert "'a': '1'" in logged[0]


def test_log_request_keeps_a_cookie_named_like_a_cookie_attribute(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    """``path`` is a legal cookie name, and a schema is free to declare a parameter with it."""
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_request(_case(), _response(request_headers={"Cookie": "path=/shop; theme=dark"}))

    assert "cookies: {'path': '/shop', 'theme': 'dark'}" in logged[0]


def test_log_response_drops_the_attributes_of_a_set_cookie_header(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    response = _response(headers={"set-cookie": ["theme=dark; Path=/; HttpOnly; Max-Age=3600"]})

    library._log_response(_case(), response)

    assert "cookies: {'theme': 'dark'}" in logged[0]


def test_log_response_sanitizes_a_json_body(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    """An endpoint that hands back a credential must not write it to the log."""
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    response = _response(content=b'{"access_token": "s3cr3t", "user": "joulu"}')

    library._log_response(_case(), response)

    assert "s3cr3t" not in logged[0]
    assert FILTERED in logged[0]
    assert "joulu" in logged[0]


def test_log_response_leaves_a_body_without_secrets_as_it_is(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_response(_case(), _response(content=b'{"name": "joulu"}'))

    assert 'body: \'{"name": "joulu"}\'' in logged[0]


def test_log_response_honours_disabled_sanitization_for_the_body(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_response(_case(enabled=False), _response(content=b'{"access_token": "s3cr3t"}'))

    assert "s3cr3t" in logged[0]


def test_log_exchange_logs_the_request_and_the_response(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)

    library._log_exchange(Mock(), _response(), _case())

    assert len(logged) == 2
    assert logged[0].startswith("Request: ")
    assert logged[1].startswith("Response: ")


def test_call_and_validate_logs_through_a_check(library: SchemathesisLibrary) -> None:
    """A failing case raises before the call returns, so logging after it would never run."""
    case = _case()

    library.call_and_validate(case)

    assert case.call_and_validate.call_args.kwargs["additional_checks"] == [library._log_exchange]


def test_call_logs_the_headers_the_keyword_was_given(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "info", logged.append)
    case = _case()
    case.call.return_value = _response()

    library.call(case, headers={"X-Trace": "abc"})

    assert any("Case headers" in message and "abc" in message for message in logged)
