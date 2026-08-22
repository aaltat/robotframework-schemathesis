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


def _response(*, body: object = None) -> Mock:
    response = Mock()
    response.request.method = "POST"
    response.request.url = "http://127.0.0.1/login"
    response.request.headers = CaseInsensitiveDict({"Content-Type": "application/json"})
    response.request.body = body
    return response


@pytest.fixture
def library() -> SchemathesisLibrary:
    return SchemathesisLibrary(url="http://127.0.0.1/openapi.json")


def test_log_case_does_not_leak_credentials(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "debug", logged.append)
    case = _case()

    library._log_case(case)

    assert len(logged) == 1
    assert SECRET not in logged[0]
    assert "s3cr3t" not in logged[0]
    assert "hunter2" not in logged[0]
    assert FILTERED in logged[0]


def test_log_case_leaves_the_case_untouched(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    """Sanitization must never mutate the case, or the real request loses its credentials."""
    monkeypatch.setattr(library, "debug", lambda message: None)
    case = _case()

    library._log_case(case)

    assert case.headers["Authorization"] == SECRET
    assert case.cookies["session"] == "s3cr3t"
    assert case.body["password"] == "hunter2"


def test_log_case_keeps_values_that_are_not_sensitive(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "debug", logged.append)

    library._log_case(_case())

    assert "schemathesis" in logged[0]
    assert "dark" in logged[0]
    assert "'userid': 42" in logged[0]


def test_log_case_honours_disabled_sanitization(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "debug", logged.append)

    library._log_case(_case(enabled=False))

    assert SECRET in logged[0]
    assert FILTERED not in logged[0]


def test_log_case_prefers_given_headers(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "debug", logged.append)
    case = _case()

    library._log_case(case, {"Authorization": "Bearer token", "X-Trace": "abc"})

    assert "Bearer token" not in logged[0]
    assert FILTERED in logged[0]
    assert "abc" in logged[0]


def test_log_request_does_not_leak_credentials(library: SchemathesisLibrary, monkeypatch: Any) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "debug", logged.append)
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
    monkeypatch.setattr(library, "debug", logged.append)
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
    monkeypatch.setattr(library, "debug", logged.append)

    library._log_request(_case(), _response(body=b'{"name": "joulu", "price": 1}'))

    assert 'body: b\'{"name": "joulu", "price": 1}\'' in logged[0]


def test_log_request_leaves_a_body_that_is_not_json_as_it_is(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "debug", logged.append)

    library._log_request(_case(), _response(body=b"<xml>not json</xml>"))

    assert "<xml>not json</xml>" in logged[0]


def test_log_request_honours_disabled_sanitization_for_the_body(
    library: SchemathesisLibrary, monkeypatch: Any
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(library, "debug", logged.append)

    library._log_request(_case(enabled=False), _response(body=b'{"password": "hunter2"}'))

    assert "hunter2" in logged[0]
