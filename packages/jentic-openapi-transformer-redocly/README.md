# jentic-openapi-transformer-redocly

## Running the tests
To run these integration tests, you would need both packages installed. You can test this setup by:

1. **Installing both packages in development mode:**

```
# From the project root
uv run pip install -e packages/jentic-openapi-transformer
uv run pip install -e packages/jentic-openapi-transformer-redocly
```

2. **Running the integration test:**

```
uv run --package jentic-openapi-transformer pytest packages/jentic-openapi-transformer/tests/test_bundle_redocly.py -v
```