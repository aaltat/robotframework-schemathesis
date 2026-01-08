import schemathesis


global_count_count = 0


@schemathesis.hook
def filter_query(ctx, query) -> bool:
    method = ctx.operation.method.lower().strip()
    if method == "put":
        global global_count_count
        global_count_count += 1
        if global_count_count > 2:
            return False
    return True
