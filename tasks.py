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
from invoke import task


@task
def lint(ctx):
    """Run linters."""
    print("Run ruff format")
    ctx.run("uv run ruff format .")
    print("Run ruff check")
    ctx.run("uv run ruff check SchemathesisLibrary")
    print("Run mypy")
    ctx.run("uv run mypy SchemathesisLibrary")
    print("Run RoboTidy")
    ctx.run("uv run robotidy")
