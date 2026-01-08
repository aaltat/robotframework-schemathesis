import schemathesis


@schemathesis.hook
def map_headers(ctx, headers):
    if headers is None:
        headers = {}
    headers["flatmap-headers"] = "I am here too"
    return headers
