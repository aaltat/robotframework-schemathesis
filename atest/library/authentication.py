from base64 import b64encode


def get_variables():
    token = b64encode(f"joulu:pukki".encode("utf-8")).decode("ascii")
    basic_auth_headers = {"Authorization": f"Basic {token}"}
    return {
        "BASIC_AUTH_HEADERS": basic_auth_headers,
    }
