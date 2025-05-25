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
from pathlib import Path
import time

import requests
from invoke.tasks import task

ROOT = Path(__file__).parent
DOCKER_IMAGE = "schemathesis-library-test"
DOCKER_CONTAINER = "schemathesis-library-test-app"


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
    for i in range(300):
        time.sleep(1)
        try:
            response = requests.get("http://127.0.0.1")
            if response.status_code == 200:
                print("Test app is running")
                break
            time.sleep(1)
        except requests.ConnectionError as error:
            print(f"Connection error: {error}")
        if i == 299:
            raise RuntimeError("Test app did not start in time")
