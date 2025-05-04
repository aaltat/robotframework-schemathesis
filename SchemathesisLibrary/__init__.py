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

from DataDriver import DataDriver  # type: ignore
from robot.running.model import TestCase, TestSuite  # type: ignore
from robot.result.model import TestSuite as ResultTestSuite  # type: ignore
from robot.result.model import TestCase as ResultTestCase  # type: ignore

__version__ = "0.1.0"


class SchemathesisLibrary:
    ROBOT_LIBRARY_VERSION = __version__
    ROBOT_LISTENER_API_VERSION = 3
    ROBOT_LIBRARY_SCOPE = "TEST SUITE"

    def __init__(self):
        self.ROBOT_LIBRARY_LISTENER = self
        self.data_driver = DataDriver()

    def _start_suite(self, data: TestSuite, result: ResultTestSuite):
        self.data_driver._start_suite(data, result)

    def _start_test(self, data: TestCase, result: ResultTestCase):
        self.data_driver._start_test(data, result)
