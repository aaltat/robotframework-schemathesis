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
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import requests
from robot.running.arguments import PythonArgumentParser
from schemathesis import Case

from src.SchemathesisLibrary import SchemathesisLibrary
from src.SchemathesisLibrary.schemathesisreader import SchemathesisReader

SCHEMA = {
    "openapi": "3.0.0",
    "info": {"title": "TLS", "version": "1"},
    "paths": {"/health": {"get": {"responses": {"200": {"description": "OK"}}}}},
}


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def send(
        _session: requests.Session, request: requests.PreparedRequest, **kwargs: Any
    ) -> requests.Response:
        calls.append(kwargs)
        response = requests.Response()
        response.status_code = 200
        response.request = request
        response.url = request.url or ""
        response._content = b""
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    return calls


def generated_case(tmp_path: Path, **library_kwargs: Any) -> tuple[SchemathesisLibrary, Case]:
    path = tmp_path / "openapi.json"
    path.write_text(json.dumps(SCHEMA))
    library = SchemathesisLibrary(
        path=path, base_url="https://localhost:48443", max_examples=1, **library_kwargs
    )
    reader_config = Mock(kwargs={}, list_separator=",")
    case = SchemathesisReader(reader_config).get_data_from_source()[0].arguments["${case}"]
    return library, case


def test_tls_verify_false_disables_verification_even_with_a_session(
    tmp_path: Path, sent: list[dict[str, Any]]
) -> None:
    library, case = generated_case(tmp_path, tls_verify=False)
    session = requests.Session()
    session.verify = False

    library.call(case, session=session)

    assert sent[-1]["verify"] is False


def test_tls_verify_false_reaches_the_requests_sent_by_checks(
    tmp_path: Path, sent: list[dict[str, Any]]
) -> None:
    _, case = generated_case(tmp_path, tls_verify=False)

    case.operation.schema.transport.send(case)

    assert sent[-1]["verify"] is False


@pytest.mark.parametrize(
    ("config", "library_kwargs", "expected"),
    [
        (None, {}, True),
        (None, {"tls_verify": False}, False),
        (None, {"tls_verify": "/etc/ssl/ca.pem"}, "/etc/ssl/ca.pem"),
        ("tls-verify = false\n", {}, False),
        ("tls-verify = false\n", {"tls_verify": True}, True),
    ],
    ids=["default", "disabled", "ca-bundle", "config-file", "argument-over-config-file"],
)
def test_tls_verify_reaches_requests(
    tmp_path: Path,
    sent: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    config: str | None,
    library_kwargs: dict[str, Any],
    expected: Any,
) -> None:
    monkeypatch.chdir(tmp_path)
    if config is not None:
        (tmp_path / "schemathesis.toml").write_text(config)
    library, case = generated_case(tmp_path, **library_kwargs)

    library.call(case)

    assert sent[-1]["verify"] == expected


@pytest.mark.parametrize(
    ("given", "expected"),
    [("False", False), ("off", False), ("True", True), ("/etc/ssl/ca.pem", "/etc/ssl/ca.pem")],
)
def test_tls_verify_given_in_robot_data_is_converted(
    tmp_path: Path, sent: list[dict[str, Any]], given: str, expected: Any
) -> None:
    spec = PythonArgumentParser().parse(SchemathesisLibrary.__init__)
    _, named = spec.convert([], [("tls_verify", given)])
    library, case = generated_case(tmp_path, **dict(named))

    library.call(case)

    assert sent[-1]["verify"] == expected
