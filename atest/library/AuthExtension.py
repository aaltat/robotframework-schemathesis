from base64 import b64encode

import schemathesis
from robot.api import logger


@schemathesis.auth().apply_to(path_regex=r"/user/.+")
class AuthExtension:
    def get(self, case, ctx):
        return b64encode("joulu:pukki".encode("utf-8")).decode("ascii")

    def set(self, case, data, ctx):
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Basic {data}"
        logger.debug(f"Updated headers for case: {case.operation.method} {case.operation.path}")
