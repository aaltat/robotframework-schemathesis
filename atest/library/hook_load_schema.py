import schemathesis


@schemathesis.hook
def before_load_schema(ctx, raw_schema) -> None:
    path = "/items/{item_id}"
    raw_schema["paths"] = {path: {"delete": raw_schema["paths"][path]["delete"]}}
