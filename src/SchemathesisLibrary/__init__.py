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
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from DataDriver import DataDriver  # type: ignore
from requests.sessions import Session
from requests.structures import CaseInsensitiveDict
from robot.api import logger
from robot.api.deco import keyword
from robot.result.model import TestCase as ResultTestCase  # type: ignore
from robot.result.model import TestSuite as ResultTestSuite  # type: ignore
from robot.running.model import TestCase, TestSuite  # type: ignore
from robot.utils.dotdict import DotDict  # type: ignore
from robotlibcore import DynamicCore  # type: ignore
from schemathesis import Case
from schemathesis.core import NotSet
from schemathesis.core.output.sanitization import sanitize_url, sanitize_value
from schemathesis.core.transport import Response

from .schemathesisreader import Options, SchemathesisReader

if TYPE_CHECKING:
    from pathlib import Path

    from schemathesis.config import SanitizationConfig

__version__ = "2.6.0"


class SchemathesisLibrary(DynamicCore):
    """SchemathesisLibrary is a library for validating API schema using Schemathesis tool.

    Example usage of the library and the [Call And Validate] keyword

    Library must be imported with the ``url`` or ``path`` argument to specify the
    OpenAPI schema. The library uses
    [DataDriver](https://github.com/Snooz82/robotframework-datadriver) to generate
    test cases from the OpenAPI schema by using
    [Schemathesis](https://github.com/schemathesis/schemathesis). The library
    creates test cases that takes one argument, ``${case}``, which is a
    Schemathesis
    [Case](https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Case)
    object. The `Call And Validate` keyword can be used to call and validate
    the case. The keyword will log the request and response details.

    # Logging And Sanitization

    Keywords log the request and response details, and credentials in those details are
    replaced with ``[Filtered]`` before anything is written to the Robot Framework log.
    Headers, cookies, path parameters, JSON request bodies and the request URL are all
    sanitized. A request body in some other format can not be inspected and is logged as it is.

    Which values count as sensitive is decided by Schemathesis, not by this library, and
    the rules are the same ones the ``schemathesis`` command line tool uses. Matching is
    done on the name of the value, both against a list of well known names such as
    ``Authorization`` and ``Cookie``, and against markers such as ``key``, ``token`` and
    ``secret`` that are looked for anywhere in the name. This means that a header named
    ``key1`` is filtered as well, because it contains the marker ``key``.

    The names, the markers and the replacement text can be changed, and sanitization can
    be turned off altogether, with the ``[output.sanitization]`` table in the
    ``schemathesis.toml`` configuration file. See the Schemathesis
    [configuration](https://schemathesis.readthedocs.io/en/stable/reference/configuration/)
    documentation for the details.

    Response bodies are **not** sanitized. If an endpoint returns a credential in its
    response body, that credential is written to the log as is.

    Example:
    ```robotframework
    *** Settings ***
    Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json

    Test Template       Wrapper

    *** Test Cases ***
    All Tests   # This test is deleted by DataDriver
        Wrapper    test_case_1

    *** Keywords ***
    Wrapper
        [Arguments]    ${case}
        Call And Validate    ${case}
    ```
    """

    ROBOT_LIBRARY_VERSION = __version__
    ROBOT_LISTENER_API_VERSION = 3
    ROBOT_LIBRARY_SCOPE = "TEST SUITE"
    ROBOT_LIBRARY_DOC_FORMAT = "Markdown"

    def __init__(  # noqa: PLR0913
        self,
        *,
        headers: "dict[str, Any]|None" = None,
        max_examples: int = 100,
        path: "Path|None" = None,
        url: "str|None" = None,
        auth: str | None = None,
        hook: str | None = None,
        strict: bool = True,
    ) -> None:
        """
        Arguments:
            headers:
                Optional HTTP headers to be used when schema is downloaded from ``url``.
                Argument is only needed when the schema is downloaded from a URL and there is need to pass example
                authentication headers to the endpoint. The ``headers`` is not used in the API calls are made during
                test execution.
            max_examples:
                Maximum number of examples to generate for each operation. Default is 100.
            path:
                Path to the OpenAPI schema file. Using either ``path`` or ``url`` is mandatory.
            url:
                URL where the OpenAPI schema can be downloaded.
            auth:
                Optional authentication class to be used passed for Schemathesis authentication when test cases are executed.
                Argument is used to create Schemathesis
                [dynamic token](https://schemathesis.readthedocs.io/en/stable/guides/auth/#dynamic-token-authentication)
                authentication for the test cases. The dynamic token generation class should follow the Schemathesis
                documentation. The only addition is the import and importing the class must follow the Robot Framework library
                [import rules](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#specifying-library-to-import).
                Example if importing with filename, filename much match to the class name. See example from
                [README.md](https://github.com/aaltat/robotframework-schemathesis?tab=readme-ov-file##dynamic-token-authentication)
                file
            hook:
                Optional Schemathesis [hook](https://schemathesis.readthedocs.io/en/stable/guides/extending/). The
                argument can be used to specify Schemathesis hooks to modify the generated test cases. The hooks
                implementation must follow the Schemathesis documentation:
                [Hooks](https://schemathesis.readthedocs.io/en/stable/guides/extending/) importing follows same
                rules as importing
                [test libraries](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#specifying-library-to-import)
                in Robot Framework. Multiple hooks can be specified by separating them with semicolon (;).
            strict:
                Whether a problem that would silently reduce test coverage is an error. Defaults to
                ``True``. See the Strict Mode section below for details.


        ``path`` and ``url`` are mutually exclusive, only one of them should be used to specify the OpenAPI schema location.

        # Configuration File

        SchemathesisLibrary automatically discovers and loads configuration from a ``schemathesis.toml`` file if present
        in the project directory. The configuration file allows you to customize test data generation and other Schemathesis
        settings without modifying the library initialization.

        The library uses Schemathesis's
        [configuration file discovery](https://schemathesis.readthedocs.io/en/stable/reference/configuration/)
        mechanism to locate ``schemathesis.toml`` in the current directory or parent directories (stopping at .git folder
        or filesystem root).

        Configuration options that are automatically applied:

        - ``max-examples``: If specified in ``[project.generation]``, overrides the ``max_examples`` parameter passed to the library
        - ``mode``: Generation mode (``positive``, ``negative``, or ``all``) controls whether valid or invalid test data is generated

        Example schemathesis.toml:
        ```toml
        [[project]]
        title = "My API"

        [project.generation]
        mode = "positive"      # Generate only valid test cases
        max-examples = 5       # Generate 5 test cases per operation
        ```

        For complete configuration options, see schemathesis
        [configuration](https://schemathesis.readthedocs.io/en/stable/reference/configuration/)
        documentation.

        If no configuration file is found, the library uses default values (POSITIVE mode and max_examples from
        library initialization.

        # Strict Mode

        Not every operation in a schema can be turned into test cases. An operation is skipped by
        Schemathesis when it can not be parsed, for example when it refers to a component that does
        not exist in the schema, or when one of its parameters is malformed. Such an operation is
        never tested.

        This is what the ``strict`` argument is about. With the default ``strict=True`` the library
        raises an error that names every operation it could not parse, and the suite does not run.
        With ``strict=False`` the operations are skipped, a warning that names them is written to the
        log, and the rest of the schema is tested as usual.

        ```robotframework
        *** Settings ***
        Library             SchemathesisLibrary
        ...                     url=http://127.0.0.1/openapi.json
        ...                     strict=False
        ```

        Choose ``strict=False`` when you knowingly work against a schema that has parts you can not
        fix, and you would rather test the parts that do work. Be aware of what it costs: the skipped
        operations are not tested, the suite still passes, and the only sign that your coverage
        shrank is a warning in the log. That is why the default is ``True``.

        ``strict`` has no effect on the case where nothing at all could be generated. If the schema
        produces no test cases whatsoever, the library always raises an error, because a suite
        without test cases passes without testing anything.

        Raises:
            ValueError: When the schema can not be turned into test cases, either because an
                operation could not be parsed and ``strict`` is ``True``, or because no test cases
                were generated at all. The error is raised when the suite starts, not when the
                library is imported.
        """
        self.ROBOT_LIBRARY_LISTENER = self
        SchemathesisReader.options = Options(
            headers=headers,
            max_examples=max_examples,
            path=path,
            url=url,
            auth=auth,
            hook=hook,
            strict=strict,
        )
        self.data_driver = DataDriver(reader_class=SchemathesisReader)
        DynamicCore.__init__(self, [])

    def _start_suite(self, data: TestSuite, result: ResultTestSuite) -> None:
        self.data_driver._start_suite(data, result)

    def _start_test(self, data: TestCase, result: ResultTestCase) -> None:
        self.data_driver._start_test(data, result)

    @keyword
    def call_and_validate(
        self,
        case: Case,
        *,
        base_url: str | None = None,
        headers: dict[str, Any] | None = None,
        auth: tuple[str, str] | Any | None = None,
        session: Session | None = None,
    ) -> Response:
        """Call and validate a Schemathesis case.

        Example:
        ```robotframework
        *** Settings ***
        Library             SchemathesisLibrary
        ...                     url=http://127.0.0.1/openapi.json
        Test Template       Wrapper

        *** Test Cases ***
        All Tests
            Wrapper    test_case_1    # Test is replaced by DataDriver with generated test cases

        *** Keywords ***
        Wrapper
            ${response} =    Call And Validate    ${case}
        ```

        Arguments:
            case:
                The Schemathesis
                [Case](https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Case)
                to be called and validated.
            base_url:
                Optional base URL to override the one defined in the schema. Need mostly when schema is read from
                a file.
            headers:
                Optional HTTP headers to be added when calling the API endpoint.
            auth:
                Optional authentication to be used when calling the case. Argument can be any authentication
                supported by [httpx authentication](https://www.python-httpx.org/advanced/authentication/).
                Example a tuple containing username and password for basic authentication or an instance of
                [Digest authentication](https://www.python-httpx.org/advanced/authentication/#digest-authentication)
            session:
                Optional request session to be used when calling the case. Argument can be used to pass
                a pre-configured HTTP session and it must be an instance of
                [requests.session.Session](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
                . If, example, session is created by using `RequestsLibrary`, then current session can be obtained
                by following way from python code:
                ```python
                from robot.libraries.BuiltIn import BuiltIn

                def get_request_session():
                    request_library = BuiltIn().get_library_instance("RequestsLibrary")
                    return request_library._cache.current
                ```

                Then this can be used in test case like:
                ```robotframework
                *** Settings ***
                Library             RequestsLibrary
                Library             SchemathesisLibrary
                ...                     url=http://127.0.0.1/openapi.json
                Library             ${CURDIR}/request_session.py
                Test Template       Wrapper

                *** Test Cases ***
                All Tests
                    Wrapper    test_case_1

                *** Keywords ***
                Wrapper
                    [Arguments]    ${case}
                    Create Session
                    ...    session    http://127.0.0.1/
                    ${session} =    Get Request Session
                    Call And Validate
                    ...    ${case}
                    ...    headers=&{BASIC_AUTH_HEADERS}
                    ...    session=${session}
                ```

        Returns:
            [Schemathesis Response](https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Response)
            object. Can be used to further validate the response, example check specific headers or response
            body.
        """
        headers = self._dot_dict_to_dict(headers) if headers else None
        self.info(f"Case: {case.path} | {case.method} | {self._sanitize(case, case.path_parameters)}")
        self._log_case(case, headers)
        if session:
            self.info("Using provided session for the request.")
        auth_kwargs = self._auth_kwargs(auth)
        response = case.call_and_validate(base_url=base_url, headers=headers, session=session, **auth_kwargs)
        self._log_request(case, response)
        self.debug(
            f"Response: {self._sanitize(case, response.headers)} | {response.status_code} | {response.text}"
        )
        return response

    @keyword
    def call(
        self,
        case: Case,
        *,
        base_url: str | None = None,
        headers: dict[str, Any] | None = None,
        auth: tuple[str, str] | Any | None = None,
        session: Session | None = None,
    ) -> Response:
        """Call a Schemathesis case without validation.

        The `Call` and `Validate Response` keywords can be used together
        to call a case and validate the response.

        ```robotframework
        *** Settings ***
        Library             SchemathesisLibrary
        ...                     url=http://127.0.0.1/openapi.json
        Test Template       Wrapper

        *** Test Cases ***
        All Tests
            Wrapper    test_case_1    # Test is replaced by DataDriver with generated test cases

        *** Keywords ***
        Wrapper
            ${response} =    Call    ${case}
            Validate Response
            ...    ${case}    ${response}
        ```

        Arguments:
            case:
                The Schemathesis
                [Case](https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Case|Case)
                to be called and validated.
            base_url:
                Optional base URL to override the one defined in the schema. Need mostly when schema is read
                from a file.
            headers:
                Optional HTTP headers to be added when calling the API endpoint.
            auth:
                Optional authentication to be used when calling the case. Argument can be any authentication
                supported by [httpx authentication](https://www.python-httpx.org/advanced/authentication/).
                Example a tuple containing username and password for basic authentication or an instance of
                [Digest authentication](https://www.python-httpx.org/advanced/authentication/#digest-authentication)
            session:
                Optional request session to be used when calling the case. See [Call And Validate] keyword
                for example of using ``session`` argument.

        Returns:
            [Schemathesis Response](https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Response)
            object. Can be used to further validate the response, example check specific headers
            or response body.
        """
        headers = self._dot_dict_to_dict(headers) if headers else None
        self.info(f"Calling case: {case.path} | {case.method} | {self._sanitize(case, case.path_parameters)}")
        self._log_case(case)
        if session:
            self.info("Using provided session for the request.")
        auth_kwargs = self._auth_kwargs(auth)
        response = case.call(base_url=base_url, headers=headers, session=session, **auth_kwargs)
        self._log_request(case, response)
        return response

    @keyword
    def validate_response(
        self,
        case: Case,
        response: Response,
        headers: dict[str, Any] | None = None,
        auth: tuple[str, str] | Any | None = None,
    ) -> None:
        """Validate a Schemathesis response.

        The response is validated against the case's expectations.
        The [Call] and [Validate Response] keywords can be used together
        to call a case and validate the response. See the example from
        [Call] keyword documentation.

        Arguments:
            case:
                The Schemathesis case to be validated against.
            response:
                The Schemathesis response to be validated. Returned by `Call` keyword.
            headers:
                Optional HTTP headers to be added when calling the API endpoint.
            auth:
                Optional authentication to be used when calling the case. Argument can be any authentication
                supported by [httpx authentication](https://www.python-httpx.org/advanced/authentication/).
                Example a tuple containing username and password for basic authentication or an instance of
                [Digest authentication](https://www.python-httpx.org/advanced/authentication/#digest-authentication)
        """
        self.info(f"Validating response: {response.status_code} | {self._sanitize(case, response.headers)}")
        transport_kwargs: dict[str, Any] = {}
        if auth:
            transport_kwargs["auth"] = auth
        if headers:
            transport_kwargs["headers"] = headers
        case.validate_response(response=response, transport_kwargs=transport_kwargs)
        self.info("Response validation passed.")

    @keyword(name="As cURL")
    def as_curl(self, case: Case) -> str:
        """Convert a Schemathesis case to a cURL command.

        Example:
        ```robotframework
        *** Settings ***
        Library             SchemathesisLibrary
        ...                     url=http://127.0.0.1/openapi.json
        Test Template       Wrapper

        *** Test Cases ***
        All Tests
            Wrapper    test_case_1    # Test is replaced by DataDriver with generated test cases

        *** Keywords ***
        Wrapper
            ${curl_command} =    `As cURL`    ${case}
            Log    ${curl_command}
        ```

        Arguments:
            case:  The Schemathesis case to be converted.

        Returns:
            Returns a string containing the cURL command that can be used to execute the same request as the case.
        """
        self.info(
            f"Converting case to cURL: {case.path} | {case.method} | {self._sanitize(case, case.path_parameters)}"
        )
        self._log_case(case)
        curl_command = case.as_curl_command()
        self.debug(f"Generated cURL command: {curl_command}")
        return curl_command

    def info(self, message: str) -> None:
        logger.info(message)

    def debug(self, message: str) -> None:
        logger.debug(message)

    def _log_case(
        self,
        case: Case,
        headers: "dict[str, Any]|None" = None,
    ) -> None:
        body = case.body if not isinstance(case.body, NotSet) else "Not set"
        case_headers = headers or case.headers
        self.debug(
            f"Case headers {self._sanitize(case, case_headers)!r} body {self._sanitize(case, body)!r} "
            f"cookies {self._sanitize(case, case.cookies)!r} "
            f"path parameters {self._sanitize(case, case.path_parameters)!r}"
        )

    def _log_request(self, case: Case, response: Response) -> None:
        self.debug(
            f"Request: {response.request.method} {self._sanitize_url(case, response.request.url)} "
            f"headers: {self._sanitize(case, response.request.headers)!r} "
            f"body: {self._sanitize_body(case, response.request.body)!r}"
        )

    def _auth_kwargs(self, auth: "tuple[str, str]|Any|None") -> dict[str, Any]:
        """Only forward ``auth`` when it is set.

        ``auth`` is not a named argument of the Schemathesis ``Case`` methods, it ends up in
        their ``**kwargs`` and overwrites whatever the transport resolved. Forwarding ``None``
        therefore silently drops the authentication an auth provider assigned to the case.
        """
        return {} if auth is None else {"auth": auth}

    def _sanitization_config(self, case: Case) -> "SanitizationConfig|None":
        config = case.operation.schema.config.output.sanitization
        return config if config.enabled else None

    def _sanitize(self, case: Case, value: Any) -> Any:
        """Return a sanitized copy of ``value``.

        Sanitization happens on a copy on purpose: ``sanitize_value`` replaces values in
        place, and sanitizing the case itself would strip the credentials off the request
        that is about to be sent.
        """
        config = self._sanitization_config(case)
        if config is None or not isinstance(value, dict | list | CaseInsensitiveDict):
            return value
        sanitized = deepcopy(value)
        sanitize_value(sanitized, config=config)
        return sanitized

    def _sanitize_body(self, case: Case, body: Any) -> Any:
        """Return a sanitized copy of a serialized request body.

        The body of the request that went out is bytes or a string, so it has to be parsed
        back into a structure before the values in it can be replaced. A body that is not
        JSON can not be inspected and is returned untouched, and so is a body that holds
        nothing sensitive, which keeps it in the exact form it was sent in.
        """
        if not isinstance(body, str | bytes):
            return self._sanitize(case, body)
        if self._sanitization_config(case) is None:
            return body
        try:
            parsed = json.loads(body)
        except (ValueError, TypeError):
            return body
        if not isinstance(parsed, dict | list):
            return body
        sanitized = self._sanitize(case, parsed)
        return body if sanitized == parsed else json.dumps(sanitized)

    def _sanitize_url(self, case: Case, url: "str|None") -> "str|None":
        config = self._sanitization_config(case)
        if config is None or url is None:
            return url
        return sanitize_url(url, config=config)

    def _dot_dict_to_dict(self, dot_dict: dict[str, Any]) -> dict[str, Any]:
        if isinstance(dot_dict, DotDict):
            return dict(dot_dict)
        return dot_dict
