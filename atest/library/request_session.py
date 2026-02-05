from robot.libraries.BuiltIn import BuiltIn


def get_request_session():
    request_library = BuiltIn().get_library_instance("RequestsLibrary")
    return request_library._cache.current
