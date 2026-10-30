import schemathesis
from requests.auth import HTTPBasicAuth

schemathesis.auth.set_from_requests(HTTPBasicAuth("joulu", "pukki")).apply_to(path_regex=r"/user/.+")
