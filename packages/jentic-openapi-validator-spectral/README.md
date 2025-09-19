# jentic-openapi-validator-spectral

## Running the tests

To run these integration tests, you would need both packages installed. You can test this setup by:

1. **Installing both packages in development mode:**

```
# From the project root
uv run pip install -e packages/jentic-openapi-validator
uv run pip install -e packages/jentic-openapi-validator-spectral
```

2. **Running the integration test:**

```
uv run --package jentic-openapi-validator pytest packages/jentic-openapi-validator/tests/test_validate_spectral.py -v
```