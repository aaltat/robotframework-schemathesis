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
import shutil
import time

import requests
from invoke.tasks import task
from robot.libdoc import libdoc

ROOT_DIR = Path(__file__).parent
ATEST_OUTPUT_DIR = ROOT_DIR / "atest" / "output_runner"
SPEC_FOLDER = ROOT_DIR / "atest" / "specs"
ATEST_OUTPUT_DIR_LIB = ROOT_DIR / "atest" / "output_library"
DIST_DIR = ROOT_DIR / "dist"
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
    ctx.run(f"uv run ruff {ruff_args}  src/SchemathesisLibrary")
    print("Run mypy")
    ctx.run("uv run mypy src/SchemathesisLibrary")
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
def docs(ctx, set_version: str | None = None):
    """Generate library keyword documentation.

    Args:
        set_version: Creates keyword documentation with version
        suffix in the name. Documentation is moved to docs/vesions
        folder.
    """
    docs_dir = ROOT_DIR / "docs"
    if not set_version:
        target = docs_dir / "SchemathesisLibrary.html"
    else:
        versions_dir = docs_dir / "versions"
        versions_dir.mkdir(parents=True, exist_ok=True)
        target = versions_dir / f"SchemathesisLibrary-{set_version}.html"
    libdir = ROOT_DIR / "src" / "SchemathesisLibrary"

    print(f"Generating documentation for {libdir} to {target}")
    libdoc(str(libdir), str(target))
    if not target.is_file():
        raise RuntimeError(f"Documentation generation failed, file not found: {target}")


@task
def old_version_docs(ctx, version: str | None = None):
    """Generate old version documentation index."""
    if not version:
        raise ValueError("Version must be provided to generate old version documentation index.")
    index = ROOT_DIR / "docs" / "versions" / "index.md"
    with index.open("a") as file:
        url = (
            "https://github.com/aaltat/robotframework-schemathesis/docs/versions/"
            f"SchemathesisLibrary-{version}.html"
        )
        file.write(f"\n[{version}]({url})\n")


@task
def spec_file(ctx):
    """Download test app open api specification file"""
    url = f"{DOCKER_APP_URL}/openapi.json"
    local_filename = url.split("/")[-1]
    if SPEC_FOLDER.is_dir():
        shutil.rmtree(SPEC_FOLDER)
    SPEC_FOLDER.mkdir(parents=True, exist_ok=True)
    local_filename = SPEC_FOLDER / local_filename
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        local_filename.open
        with local_filename.open("wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    print(f"Test app open api spec file {local_filename} downloaded successfully.")


@task(pre=[test_app, spec_file])
def atest(ctx):
    """Run acceptance tests."""
    args = [
        "uv",
        "run",
        "robot",
        "--loglevel",
        "DEBUG:INFO",
        "--pythonpath",
        "./src",
        "--outputdir",
        ATEST_OUTPUT_DIR.as_posix(),
        "atest/test",
    ]
    shutil.rmtree(ATEST_OUTPUT_DIR, ignore_errors=True)
    shutil.rmtree(ATEST_OUTPUT_DIR_LIB, ignore_errors=True)
    ATEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ATEST_OUTPUT_DIR_LIB.mkdir(parents=True, exist_ok=True)
    print(f"Running {args}")
    ctx.run(" ".join(args))


@task
def clean(ctx):
    """Clean up the output and dist directories."""
    print("Cleaning up output directories...")
    shutil.rmtree(ATEST_OUTPUT_DIR, ignore_errors=True)
    shutil.rmtree(ATEST_OUTPUT_DIR_LIB, ignore_errors=True)
    print("Cleaning up dist directories...")
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    print("directories cleaned.")
