import schemathesis


@schemathesis.hook
def map_headers(ctx, headers):
    if headers is None:
        headers = {}
    headers["map-headers"] = "I am here"
    return headers
