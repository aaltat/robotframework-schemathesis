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
from robot.utils.dotdict import DotDict  # type: ignore
from schemathesis.config._output import SanitizationConfig

from src.SchemathesisLibrary import SchemathesisLibrary


@pytest.fixture
def library() -> SchemathesisLibrary:
    return SchemathesisLibrary(path="openapi.json")


@pytest.fixture
def case() -> Mock:
    case = Mock()
    case.operation.schema.config.output.sanitization = SanitizationConfig()
    case.formatted_path = "/user/1"
    return case


def response_to(url: str) -> Mock:
    response = Mock()
    response.request.url = url
    response.status_code = 200
    response.headers = {}
    return response


def test_base_url_is_taken_from_where_the_response_was_sent_to(
    library: SchemathesisLibrary, case: Mock
) -> None:
    """The checks' extra requests must go to the same server that answered."""
    library.validate_response(case, response_to("http://127.0.0.1:8000/api/v1/user/1?q=x"))

    transport_kwargs = case.validate_response.call_args.kwargs["transport_kwargs"]
    assert transport_kwargs["base_url"] == "http://127.0.0.1:8000/api/v1"


def test_keyword_base_url_wins_over_where_the_response_was_sent_to(
    library: SchemathesisLibrary, case: Mock
) -> None:
    library.validate_response(case, response_to("http://127.0.0.1/user/1"), base_url="http://other:9000/api")

    transport_kwargs = case.validate_response.call_args.kwargs["transport_kwargs"]
    assert transport_kwargs["base_url"] == "http://other:9000/api"


def test_library_base_url_is_used_and_warned_about_when_the_response_url_does_not_match(
    library: SchemathesisLibrary, case: Mock, monkeypatch: Any
) -> None:
    """A redirect, for example, leaves nothing to cut the operation path off."""
    warned: list[str] = []
    monkeypatch.setattr(library, "warn", warned.append)
    case.operation.schema.get_base_url.return_value = "http://staging/api"

    library.validate_response(case, response_to("http://127.0.0.1/login"))

    transport_kwargs = case.validate_response.call_args.kwargs["transport_kwargs"]
    assert transport_kwargs["base_url"] == "http://staging/api"
    assert len(warned) == 1
    assert "http://127.0.0.1/login" in warned[0]
    assert "http://staging/api" in warned[0]


def test_raises_when_no_base_url_is_known(library: SchemathesisLibrary, case: Mock) -> None:
    """A file-loaded schema without servers gives Schemathesis nowhere to send the checks' extra requests."""
    case.operation.schema.get_base_url.return_value = "file:///"

    with pytest.raises(ValueError, match=r"pass base_url= to the keyword or on library import"):
        library.validate_response(case, response_to("http://127.0.0.1/login"))

    case.validate_response.assert_not_called()


def test_headers_are_given_to_the_checks_as_a_plain_dict(library: SchemathesisLibrary, case: Mock) -> None:
    """Checks such as ignored_auth read the headers from their own argument, not from transport_kwargs."""
    library.validate_response(case, response_to("http://127.0.0.1/user/1"), headers=DotDict(key1="value1"))

    kwargs = case.validate_response.call_args.kwargs
    for headers in (kwargs["headers"], kwargs["transport_kwargs"]["headers"]):
        assert type(headers) is dict
        assert headers == {"key1": "value1"}
