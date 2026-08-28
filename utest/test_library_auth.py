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
from unittest.mock import Mock

import pytest
from requests.auth import HTTPDigestAuth
from requests.structures import CaseInsensitiveDict
from schemathesis.config._output import SanitizationConfig

from src.SchemathesisLibrary import SchemathesisLibrary

AUTH = ("joulu", "pukki")


@pytest.fixture
def library() -> SchemathesisLibrary:
    return SchemathesisLibrary(url="http://127.0.0.1/openapi.json")


@pytest.fixture
def case() -> Mock:
    case = Mock()
    case.operation.schema.config.output.sanitization = SanitizationConfig()
    for response in (case.call_and_validate.return_value, case.call.return_value):
        response.request.url = "http://127.0.0.1/user/1"
        response.request.headers = CaseInsensitiveDict()
        response.request.body = None
        response.status_code = 200
        response.headers = {}
        response.text_lossy = lambda: ""
    return case


def test_call_and_validate_does_not_forward_auth_when_it_is_not_given(
    library: SchemathesisLibrary, case: Mock
) -> None:
    """A None auth would overwrite the auth an auth provider assigned to the case."""
    library.call_and_validate(case)

    assert "auth" not in case.call_and_validate.call_args.kwargs


def test_call_and_validate_forwards_auth_when_it_is_given(library: SchemathesisLibrary, case: Mock) -> None:
    library.call_and_validate(case, auth=AUTH)

    assert case.call_and_validate.call_args.kwargs["auth"] == AUTH


def test_call_and_validate_forwards_auth_objects(library: SchemathesisLibrary, case: Mock) -> None:
    auth = HTTPDigestAuth("joulu", "pukki")

    library.call_and_validate(case, auth=auth)

    assert case.call_and_validate.call_args.kwargs["auth"] is auth


def test_call_does_not_forward_auth_when_it_is_not_given(library: SchemathesisLibrary, case: Mock) -> None:
    library.call(case)

    assert "auth" not in case.call.call_args.kwargs


def test_call_forwards_auth_when_it_is_given(library: SchemathesisLibrary, case: Mock) -> None:
    library.call(case, auth=AUTH)

    assert case.call.call_args.kwargs["auth"] == AUTH
