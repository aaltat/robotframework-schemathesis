from collections import defaultdict

from robot.api import ExecutionResult, ResultVisitor, logger
from robot.result.model import TestCase


class ExecutionTimeChecker(ResultVisitor):
    def __init__(self, names: dict[str, int]):
        self.names = names
        self.visited_names = defaultdict(int)
        self.test_count = 0

    def visit_test(self, test: TestCase):
        self.test_count += 1
        if name := self._test_found(test):
            self.visited_names[name] += 1
            if self.visited_names[name] > self.names[name]:
                test.status = "FAIL"
        else:
            test.status = "FAIL"

    def _test_found(self, test: TestCase):
        for name in self.names:
            if name in test.name:
                return name
        return False


class TestSuiteChecker:
    def check_suite(self, output_xml: str, test_count: int, test_description: dict[str, int]):
        """Check the test suite for execution time."""
        result = ExecutionResult(output_xml)
        checker = ExecutionTimeChecker(test_description)
        result.visit(checker)
        result.save(output_xml)
        assert checker.test_count == test_count, (
            f"Expected {test_count} tests, but found {checker.test_count}."
        )
        for name, count in test_description.items():
            assert checker.visited_names[name] == count, (
                f"Expected {count} executions of '{name}', but found {checker.visited_names[name]}."
            )
        logger.info(f"Checked test suite in {output_xml}")
