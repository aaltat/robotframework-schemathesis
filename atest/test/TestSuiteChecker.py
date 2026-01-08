from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict

from robot.api import ExecutionResult, ResultVisitor, logger
from robot.libraries.BuiltIn import BuiltIn
from robot.model import Keyword, Message
from robot.result.model import TestCase, Keyword
from robot.result.executionerrors import ExecutionErrors


@dataclass
class TestCaseData:
    name: str
    count: int
    kw_logs_to_collect: str
    logs: list[str]


class ExecutionSuiteChecker(ResultVisitor):
    def __init__(self):
        self.suite_errors = []

    def visit_errors(self, errors: ExecutionErrors):
        for error in errors:
            logger.info(f"Errors found in the suite: {error}")
            self.suite_errors.append(error.message)


class ExecutionChecker(ResultVisitor):
    def __init__(self, test_description: list[TestCaseData]):
        self.test_description = test_description
        self.visited_names = defaultdict(int)
        self.test_count = 0
        self.names = []
        self.not_expected_test = defaultdict(int)
        self.received_test_logs = defaultdict(list)
        self.current_test = None

    def visit_test(self, test: TestCase):
        self.test_count += 1
        if name := self._test_found(test):
            self.visited_names[name] += 1
        else:
            self.not_expected_test[test.name] += 1
        self.current_test = test.name
        return super().visit_test(test)

    def visit_message(self, message: Message):
        if self._is_keyword_to_collect(message):
            self.received_test_logs[self.current_test].append(message.message)
        return super().visit_message(message)

    def _test_found(self, test: TestCase):
        if not self.names:
            self.names = [t.name for t in self.test_description]
        for name in self.names:
            if name in test.name:
                return name
        return False

    def _is_keyword_to_collect(self, message: Message):
        if not message.parent:
            return False
        if not isinstance(message.parent, Keyword):
            return False
        if not hasattr(message.parent, "kwname"):
            return False
        kw_name = str(message.parent.kwname)
        kw_name = self._normalize_kw_name(kw_name)
        for test in self.test_description:
            kw_logs_to_collect = self._normalize_kw_name(test.kw_logs_to_collect)
            if kw_name == kw_logs_to_collect:
                return True
        return False

    def _normalize_kw_name(self, name: str) -> str:
        return name.replace(" ", "").replace("_", "").lower()


class ExecutionCountChecker(ResultVisitor):
    def __init__(self):
        self.test_names_counts = defaultdict(int)
        self.test_count = 0

    def visit_test(self, test: TestCase):
        self.test_count += 1
        test_name = test.name.split(" ")[0]
        self.test_names_counts[test_name] += 1
        return super().visit_test(test)


class ExecutionLogChecker(ResultVisitor):
    def __init__(self, match_start: str, kw_name: str = "Call And Validate"):
        self.match_start = match_start
        self.kw_name = kw_name.lower()
        self.test_logs = {}

    def visit_message(self, message: Message):
        if not message.message.startswith(self.match_start):
            return super().visit_message(message)
        if not (
            message.parent
            and isinstance(message.parent, Keyword)
            and message.parent.name.lower() == self.kw_name
        ):
            return super().visit_message(message)
        parent = message.parent
        while not isinstance(parent, TestCase):
            if not parent.parent:
                return super().visit_message(message)
            parent = parent.parent
        test = parent
        logger.debug(f"test case: {test}, message: {message.message}")
        self.test_logs[test.name] = message.message
        return super().visit_message(message)


class TestSuiteChecker:
    def check_suite(self, output_xml: str, test_description: list[TestCaseData]):
        """Check the test suite for test cases names."""
        test_count = 0
        for test in test_description:
            test_count += test.count
        result = ExecutionResult(output_xml)
        checker = ExecutionChecker(test_description)
        result.visit(checker)
        result.save(output_xml)
        assert checker.test_count == test_count, (
            f"Expected {test_count} tests, but found {checker.test_count}."
        )
        logger.info(f"Found {checker.test_count} tests in the suite.")
        for test in test_description:
            logger.info(f"Checking test '{test.name}'")
            assert checker.visited_names[test.name] == test.count, (
                f"Expected {test.count} occurrences of test '{test.name}', "
                f"but found {checker.visited_names[test.name]}."
            )
        assert not checker.not_expected_test, (
            f"Unexpected tests found: {', '.join(checker.not_expected_test)}"
        )
        logger.info(f"No unexpected test cases found: {len(checker.not_expected_test)}")
        should_match = BuiltIn().should_match
        for test in test_description:
            logger.info(f"Checking logs for all tests starting with '{test.name}'")
            self._check_test_logs(test.name, test.logs, checker.received_test_logs, should_match)
        logger.info(f"Checked test suite in {output_xml}")

    def check_test_names_and_counts(
        self, output_xml: str, min_count: int, max_count: int, expected_names_and_counts: dict[str, int]
    ):
        """Check the test case start with correct names and has correct number of test cases."""
        result = ExecutionResult(output_xml)
        checker = ExecutionCountChecker()
        result.visit(checker)
        result.save(output_xml)
        logger.info(f"Checked test suite in {output_xml}")
        assert checker.test_count >= min_count, (
            f"Expected at least {min_count} tests, but found {checker.test_count}."
        )
        assert checker.test_count <= max_count, (
            f"Expected at most {max_count} tests, but found {checker.test_count}."
        )
        for test_name, count in expected_names_and_counts.items():
            assert test_name in checker.test_names_counts, (
                f"Expected test name {test_name} not found in {checker.test_names_counts.keys()} "
            )
            assert checker.test_names_counts[test_name] >= count, (
                f"Expected {count} for test name {test_name} but it was {checker.test_names_counts[test_name]}"
            )

    def check_specific_test_logs(
        self,
        output_xml: str,
        log_message_start: str,
        kw_name: str = "Call And Validate",
        number_of_tests: int = 15,
        string_in_log: None | str = None,
    ):
        assert number_of_tests > 0, "number_of_tests must be greater than 0"
        assert string_in_log, "string_in_log must be provided"
        result = ExecutionResult(output_xml)
        checker = ExecutionLogChecker(log_message_start, kw_name)
        result.visit(checker)
        result.save(output_xml)
        logger.info(f"Checked test suite in {output_xml}")
        assert len(checker.test_logs) == number_of_tests, (
            f"Expected {number_of_tests} tests with logs starting with '{log_message_start}', "
            f"but found {len(checker.test_logs)}."
        )
        for test, log in checker.test_logs.items():
            logger.info(f"Checking log for test '{test}': {log}")
            assert string_in_log in log, (
                f"Expected log to contain '{string_in_log}', but it was not found in log: {log} in test '{test}'."
            )
        logger.debug(f"Found logs for tests: {checker.test_logs}")

    def _check_test_logs(
        self,
        test_name: str,
        except_logs: list[str],
        received_logs: dict[str, list[str]],
        matcher: Callable,
    ):
        received_logs_count = 0
        except_count = -1
        for test in received_logs:
            received_logs_count = 0
            if test.startswith(test_name):
                logger.info(f"Checking logs for test '{test}'")
                logs = received_logs[test]
                except_count = len(except_logs)
                for expect_log in except_logs:
                    for received_log in logs:
                        if self._match_found(expect_log, received_log, matcher):
                            received_logs_count += 1
                            break
                    else:
                        line = "\n".join(logs)
                        parts = [
                            "from:\n",
                            line,
                            f"\n\tfor test '",
                            test_name,
                            "'",
                        ]
                        line = "".join(parts)
                        raise AssertionError(f"The expected log '{expect_log}' is not found {line}")
                logger.info(f"Logs for test '{test}' are OK.")
                if received_logs_count != except_count:
                    raise AssertionError(
                        f"Expected {except_count} logs for test '{test_name}', but found {received_logs_count}."
                    )

    def _match_found(self, except_log: str, log: str, matcher: Callable) -> bool:
        try:
            matcher(log, except_log)
        except AssertionError:
            return False
        logger.debug(f"Log '{log}' matches expected log '{except_log}'")
        return True

    def check_suite_with_logs(self, output_xml: str, logs: list[str]):
        """Check the test suite for test cases names and logs."""
        result = ExecutionResult(output_xml)
        checker = ExecutionSuiteChecker()
        result.visit(checker)
        result.save(output_xml)
        should_match = BuiltIn().should_match
        for suite_error in checker.suite_errors:
            for log in logs:
                try:
                    return should_match(suite_error, log)
                except AssertionError:
                    pass
        raise AssertionError(
            f"Expected one of the logs to match suite error messages, but found none. "
            f"Suite errors: {checker.suite_errors}, logs: {logs}"
        )
