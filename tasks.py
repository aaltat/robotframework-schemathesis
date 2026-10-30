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
import shlex
import time

import requests
from invoke.tasks import task
from robot.libdoc import libdoc

ROOT_DIR = Path(__file__).parent
ATEST_OUTPUT_DIR = ROOT_DIR / "atest" / "output_runner"
SPEC_FOLDER = ROOT_DIR / "atest" / "specs" / "test-app"
ATEST_OUTPUT_DIR_LIB = ROOT_DIR / "atest" / "output_library"
DIST_DIR = ROOT_DIR / "dist"
DOCKER_IMAGE = "schemathesis-library-test"
DOCKER_CONTAINER = "schemathesis-library-test-app"
DOCKER_APP_URL = "http://127.0.0.1"
DOCKER_APP_TLS_URL = "https://127.0.0.1:8443"
# The library runs in Robot Framework processes started by pabot and by the runner suites,
# with varying working directories. Coverage starts itself in each of those from this environment.
COVERAGE_ENV = {
    "COVERAGE_PROCESS_START": (ROOT_DIR / "pyproject.toml").as_posix(),
    "COVERAGE_FILE": (ROOT_DIR / ".coverage").as_posix(),
}


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
    ctx.run("uv run robocop format")


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
    ctx.run(f"docker run -d --name {DOCKER_CONTAINER} -p 80:80 -p 8443:8443 {DOCKER_IMAGE}")
    _wait_for_app(DOCKER_APP_URL)
    # The HTTPS listener uses a self-signed certificate, so it can not be verified here.
    _wait_for_app(DOCKER_APP_TLS_URL, verify=False)


def _wait_for_app(url: str, verify: bool = True):
    try_count = 120
    for i in range(try_count):
        time.sleep(1)
        try:
            response = requests.get(url, verify=verify)
            if response.status_code == 200:
                print(f"Test app is running: {url}")
                break
            time.sleep(1)
        except requests.ConnectionError as error:
            print(f"Connection error: {error}")
        if i == try_count - 1:
            raise RuntimeError(f"Test app did not start in time: {url}")


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
            "https://aaltat.github.io/robotframework-schemathesis/versions/"
            f"SchemathesisLibrary-{version}.html"
        )
        file.write(f"\n[{version}]({url})\n")


@task
def version(ctx, version: str):
    """Set the version of the library __init__.py."""
    init_file = ROOT_DIR / "src" / "SchemathesisLibrary" / "__init__.py"
    with init_file.open("r") as file:
        lines = file.readlines()
    for index, line in enumerate(lines):
        if line.startswith("__version__"):
            lines[index] = f'__version__ = "{version}"\n'
            break
    with init_file.open("w") as file:
        file.writelines(lines)
    print(f"Library version set to {version} in {init_file}.")


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


@task
def utest(ctx):
    """Run unit tests."""
    marker = 90
    print("*" * marker)
    print("Running unit tests with coverage...")
    ctx.run("uv run coverage erase")
    ctx.run("uv run coverage run -m pytest -v utest")
    _coverage_report(ctx)
    print("*" * marker)


def _coverage_report(ctx, append: bool = False):
    """Combine coverage data files, create HTML report and print summary to console.

    Args:
        append: Adds the data files to existing combined data, instead of replacing it.
    """
    ctx.run(f"uv run coverage combine{' --append' if append else ''}")
    ctx.run("uv run coverage html")
    ctx.run("uv run coverage report")


@task(pre=[test_app, spec_file, utest])
def atest(ctx, suite: str | None = None):
    """Run acceptance tests."""

    args = [
        "uv",
        "run",
        "pabot",
        "--ordering",
        "atest/test/pabotsuitenames",
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
    try:
        ctx.run(" ".join(args), env=COVERAGE_ENV)
    finally:
        _coverage_report(ctx, append=True)


@task(pre=[test_app, spec_file])
def atest_lib(ctx, suite: str | None = None):
    """Run library tests."""
    args = [
        "uv",
        "run",
        "robot",
        "--loglevel",
        "DEBUG:INFO",
        "--pythonpath",
        "./src",
        "--outputdir",
        ATEST_OUTPUT_DIR_LIB.as_posix(),
    ]
    if suite:
        args.append(f"--suite")
        args.append(suite)
    args.append("atest/library")
    shutil.rmtree(ATEST_OUTPUT_DIR, ignore_errors=True)
    shutil.rmtree(ATEST_OUTPUT_DIR_LIB, ignore_errors=True)
    ATEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ATEST_OUTPUT_DIR_LIB.mkdir(parents=True, exist_ok=True)
    print(f"Running {args}")
    ctx.run("uv run coverage erase")
    try:
        ctx.run(shlex.join(args), env=COVERAGE_ENV)
    finally:
        _coverage_report(ctx)


@task
def clean(ctx):
    """Clean up the output and dist directories."""
    print("Cleaning up output directories...")
    shutil.rmtree(ATEST_OUTPUT_DIR, ignore_errors=True)
    shutil.rmtree(ATEST_OUTPUT_DIR_LIB, ignore_errors=True)
    print("Cleaning up dist directories...")
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    print("Clean specs directory...")
    shutil.rmtree(SPEC_FOLDER, ignore_errors=True)
    print("directories cleaned.")
