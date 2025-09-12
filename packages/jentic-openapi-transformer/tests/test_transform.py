from jentic_openapi_transformer import normalize


def test_normalize_adds_marker():
    doc = normalize('{"openapi":"3.1.0","info":{"title":"t","version":"1"}}')
    assert doc["x-jentic"]["transformed"] is True
    assert doc["openapi"] == "3.1.0"
