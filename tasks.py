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
from collections import defaultdict
from pathlib import Path
import time

import requests
from invoke.tasks import task
from robot.libdoc import libdoc
from robot.api import ExecutionResult, ResultVisitor
from robot.result.model import TestCase

ROOT_DIR = Path(__file__).parent
ATEST_OUTPUT_DIR = ROOT_DIR / "atest" / "output"
DOCKER_IMAGE = "schemathesis-library-test"
DOCKER_CONTAINER = "schemathesis-library-test-app"
DOCKER_APP_URL = "http://127.0.0.1"


@task
def lint(ctx, fix=False):
    """Run linters."""
    print("Run ruff format")
    ctx.run("uv run ruff format .")
    print("Run ruff check")
    ruff_args = "check --fix" if fix else "check"
    ctx.run(f"uv run ruff {ruff_args}  SchemathesisLibrary")
    print("Run mypy")
    ctx.run("uv run mypy SchemathesisLibrary")
    print("Run RoboTidy")
    ctx.run("uv run robotidy")


@task
def stop(ctx):
    """Stop and remove the test app container+image."""
    try:
        ctx.run(f"docker stop {DOCKER_CONTAINER}")
    except Exception as error:
        print(f"Error stopping container: {error}")
    try:
        ctx.run(f"docker rm {DOCKER_CONTAINER}")
    except Exception as error:
        print(f"Error removing container: {error}")
    try:
        ctx.run(f"docker image rm {DOCKER_IMAGE}")
    except Exception as error:
        print(f"Error removing image: {error}")


@task(pre=[stop])
def test_app(ctx):
    """Build docker image and start the test app."""
    ctx.run(f"docker build -t {DOCKER_IMAGE} .")
    ctx.run(f"docker run -d --name {DOCKER_CONTAINER} -p 80:80 {DOCKER_IMAGE}")
    try_count = 120
    for i in range(try_count):
        time.sleep(1)
        try:
            response = requests.get(DOCKER_APP_URL)
            if response.status_code == 200:
                print(f"Test app is running: {DOCKER_APP_URL}")
                break
            time.sleep(1)
        except requests.ConnectionError as error:
            print(f"Connection error: {error}")
        if i == try_count - 1:
            raise RuntimeError("Test app did not start in time")


@task
def docs(ctx, version: str | None = None):
    """Generate library keyword documentation.

    Args:
        version: Creates keyword documentation with version
        suffix in the name. Documentation is moved to docs/vesions
        folder.
    """
    output = ROOT_DIR / "docs" / "SchemathesisLibrary.html"
    libdoc("SchemathesisLibrary", str(output))
    if version is not None:
        target = ROOT_DIR / "docs" / "versions" / f"SchemathesisLibrary-{version.replace('v', '')}.html"
        output.rename(target)


class ExecutionTimeChecker(ResultVisitor):
    def __init__(self, names: dict[str, int]):
        self.names = names
        self.visited_names = defaultdict(int)

    def visit_test(self, test: TestCase):
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


def check_tests(output_xml):
    result = ExecutionResult(output_xml)
    test = {
        "DELETE /": 5,
        "PUT /": 5,
        "GET / ": 1,
        "GET /items/{item_id}": 5,
    }
    result.visit(ExecutionTimeChecker(test))
    result.save(output_xml)


@task(pre=[test_app])
def atest(ctx):
    """Run acceptance tests."""
    args = [
        "uv",
        "run",
        "robot",
        "--loglevel",
        "DEBUG",
        "--pythonpath",
        ".",
        "--outputdir",
        ATEST_OUTPUT_DIR.as_posix(),
        "--log",
        "NONE",
        "--report",
        "NONE",
        "atest/test",
    ]
    ATEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ctx.run(" ".join(args))
    output_xml = ATEST_OUTPUT_DIR / "output.xml"
    check_tests(output_xml.as_posix())
    log_file = ATEST_OUTPUT_DIR / "log.html"
    report_file = ATEST_OUTPUT_DIR / "report.html"
    rebot_args = [
        "uv",
        "run",
        "rebot",
        "--log",
        log_file.as_posix(),
        "--report",
        report_file.as_posix(),
        output_xml.as_posix(),
    ]
    ctx.run(" ".join(rebot_args))
