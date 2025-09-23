from jentic_openapi_validator import OpenAPIValidator


def test_validator_ok():
    val = OpenAPIValidator(["openapi-spec-validator"])
    res = val.validate('{"openapi":"3.1.0","info":{"title":"ok","version":"1"}, "paths": {}}')
    assert res.valid is True


def test_validator_failure():
    val = OpenAPIValidator(["openapi-spec-validator"])
    res = val.validate('{"openapi":"3.1.0","info":{"title":"ok","version":1}}')
    assert res.valid is False
