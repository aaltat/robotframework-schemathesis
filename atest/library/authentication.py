from base64 import b64encode


def get_variables():
    user = "joulu"
    password = "pukki"
    token = b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    basic_auth_headers = {"Authorization": f"Basic {token}"}
    return {
        "BASIC_AUTH_HEADERS": basic_auth_headers,
        "BASIC_AUTH_TUPLE": (user, password),
    }
