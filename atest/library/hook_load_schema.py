import schemathesis


@schemathesis.hook
def before_load_schema(ctx, raw_schema) -> None:
    raw_schema["paths"] = {"/items/{item_id}": {"delete": raw_schema["paths"]["/items/{item_id}"]["delete"]}}
