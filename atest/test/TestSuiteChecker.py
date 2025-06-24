from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from robot.api import ExecutionResult, ResultVisitor, logger
from robot.libraries.BuiltIn import BuiltIn
from robot.model import Keyword, Message
from robot.result.model import TestCase, Keyword
from robot.result.executionerrors import ExecutionErrors


@dataclass
class LogsDescription:
    count: int
    logs: list[str]


@dataclass
class TestCaseData:
    name: str
    count: int
    kw_logs_to_collect: str
    logs: LogsDescription


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
        kw_name = kw_name.replace(" ", "").replace("_", "").lower()
        for test in self.test_description:
            kw_logs_to_collect = test.kw_logs_to_collect.replace(" ", "").replace("_", "").lower()
            if kw_name == kw_logs_to_collect:
                return True
        return False


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

    def _check_test_logs(
        self,
        test_name: str,
        except_logs: LogsDescription,
        received_logs: dict[str, list[str]],
        matcher: Callable,
    ):
        received_logs_count = 0
        for test in received_logs:
            if test.startswith(test_name):
                logger.info(f"Checking logs for test '{test}'")
                logs = received_logs[test]
                except_logs.count

                for expect_log in except_logs.logs:
                    for received_log in logs:
                        if self._match_found(expect_log, received_log, matcher):
                            received_logs_count += 1
        if not received_logs_count == int(except_logs.count):
            raise AssertionError(
                f"Expected {except_logs.count} logs for test '{test_name}', but found {received_logs_count}."
            )

    def _match_found(self, except_log: str, log: str, matcher: Callable) -> bool:
        try:
            matcher(log, except_log)
        except AssertionError:
            return False
        logger.info(f"Log '{log}' matches expected log '{except_log}'")
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
