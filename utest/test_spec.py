from pathlib import Path

import schemathesis

root = Path(__file__).parent.parent
api_spec = root / "test_app" / "openapi.json"

schema = schemathesis.from_path(api_spec, base_url="http://localhost:8000")


@schema.parametrize()
def test_api(case):
    case.call_and_validate()
