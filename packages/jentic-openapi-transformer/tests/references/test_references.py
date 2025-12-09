"""Tests for OpenAPI reference URL processing functionality."""

from typing import Any

from jentic.apitools.openapi.parser.core import json_dumps
from jentic.apitools.openapi.transformer.core.references import (
    RewriteOptions,
    find_relative_urls,
    rewrite_urls_inplace,
)


def test_references(root_relative_refs_doc: Any) -> None:
    """Test comprehensive reference processing functionality.

    Tests:
    - Finding relative URLs in OpenAPI documents
    - Rewriting relative URLs to absolute URLs
    - Verifying that fragment-only refs are excluded
    """
    spec_doc = root_relative_refs_doc

    # Test find_relative_urls
    relative_urls = find_relative_urls(spec_doc)
    assert len(relative_urls) > 0, "Should find relative URLs in the test fixture"

    # Verify that found URLs are actually relative
    for json_path, key, value in relative_urls:
        assert not value.startswith("http://") and not value.startswith("https://"), (
            f"Found URL should be relative: {value}"
        )
        assert not value.startswith("#"), f"Fragment-only refs should not be included: {value}"

    # Test rewrite_urls_inplace
    original_count = len(relative_urls)
    base_url = "http://localhost:8080/root-relative-refs.json"
    opts = RewriteOptions(
        base_url=base_url,
        original_base_url=base_url,
        include_absolute_urls=False,
    )
    changed = rewrite_urls_inplace(spec_doc, opts)

    assert changed > 0, "Should have rewritten some URLs"
    assert changed == original_count, (
        f"Should have rewritten all {original_count} relative URLs, but changed {changed}"
    )

    # Verify that URLs were actually rewritten to absolute
    new_relative_urls = find_relative_urls(spec_doc)
    assert len(new_relative_urls) == 0, "After rewriting, there should be no relative URLs left"

    # Verify the rewritten document contains absolute URLs
    spec_text = json_dumps(spec_doc)
    assert "http://localhost:8080/" in spec_text, "Rewritten document should contain absolute URLs"


def test_references_retarget_absolute_urls(root_relative_refs_doc: Any) -> None:
    """Test retargeting absolute URLs from one base to another.

    This test verifies that when include_absolute_urls=True and original_base_url
    is specified, absolute URLs that start with the original base are rewritten
    to use the new base URL.
    """
    spec_doc = root_relative_refs_doc

    # First make some URLs absolute with original base
    opts1 = RewriteOptions(base_url="http://old.example.com/api/")
    rewrite_urls_inplace(spec_doc, opts1)

    # Add an absolute URL that matches the original base
    spec_doc["info"]["termsOfService"] = "http://old.example.com/api/terms.html"

    # Now retarget from old base to new base
    opts2 = RewriteOptions(
        base_url="https://new.example.com/v2/",
        original_base_url="http://old.example.com/api/",
        include_absolute_urls=True,
    )
    changed = rewrite_urls_inplace(spec_doc, opts2)

    assert changed > 0, "Should have retargeted some absolute URLs"

    # Verify the retargeting worked
    assert spec_doc["info"]["termsOfService"] == "https://new.example.com/v2/terms.html", (
        "Should retarget absolute URL"
    )

    # Check that some $ref was also retargeted
    spec_text = json_dumps(spec_doc)
    assert "https://new.example.com/v2/" in spec_text, "Document should contain retargeted URLs"


def test_references_refs_only(root_relative_refs_doc: Any) -> None:
    """Test reference processing with refs_only=True.

    Tests:
    - Finding only $ref fields in OpenAPI documents
    - Rewriting only $ref fields to absolute URLs
    - Verifying other URL fields are not affected
    """
    spec_doc = root_relative_refs_doc

    # Add some non-$ref URL fields to test
    spec_doc["info"]["contact"] = {"url": "./contact.html"}
    spec_doc["externalDocs"] = {"url": "./docs.html"}

    # Test find_relative_urls with refs_only=True
    relative_urls_refs_only = find_relative_urls(spec_doc, refs_only=True)
    relative_urls_all = find_relative_urls(spec_doc, refs_only=False)

    # Should find fewer URLs with refs_only=True
    assert len(relative_urls_refs_only) < len(relative_urls_all), (
        "refs_only=True should find fewer URLs than refs_only=False"
    )

    # Verify that only $ref fields are in the refs_only list
    for json_path, key, value in relative_urls_refs_only:
        assert key == "$ref", f"With refs_only=True, should only find $ref fields, but found: {key}"

    # Test rewrite_urls_inplace with refs_only=True
    base_url = "http://localhost:8080/root-relative-refs.json"
    opts = RewriteOptions(
        base_url=base_url,
        original_base_url=base_url,
        include_absolute_urls=False,
        refs_only=True,
    )
    changed = rewrite_urls_inplace(spec_doc, opts)

    assert changed > 0, "Should have rewritten some $ref URLs"
    assert changed == len(relative_urls_refs_only), (
        f"Should have rewritten all {len(relative_urls_refs_only)} $ref URLs, but changed {changed}"
    )

    # Verify that $refs were rewritten but other URL fields were not
    assert spec_doc["info"]["contact"]["url"] == "./contact.html", (
        "Non-$ref URL fields should not be affected"
    )
    assert spec_doc["externalDocs"]["url"] == "./docs.html", (
        "Non-$ref URL fields should not be affected"
    )

    # Verify that $refs were actually rewritten to absolute
    new_relative_refs = find_relative_urls(spec_doc, refs_only=True)
    assert len(new_relative_refs) == 0, "After rewriting, there should be no relative $refs left"


def test_references_retarget_absolute_urls_refs_only(root_relative_refs_doc: Any) -> None:
    """Test retargeting absolute $ref URLs with refs_only=True.

    This test verifies that when refs_only=True, include_absolute_urls=True and
    original_base_url is specified, only absolute $ref URLs are retargeted,
    not other URL fields.
    """
    spec_doc = root_relative_refs_doc

    # First make some $refs absolute with original base
    opts1 = RewriteOptions(base_url="http://old.example.com/api/", refs_only=True)
    rewrite_urls_inplace(spec_doc, opts1)

    # Add some non-$ref URL fields with the old base
    spec_doc["info"]["termsOfService"] = "http://old.example.com/api/terms.html"
    spec_doc["info"]["contact"] = {"url": "http://old.example.com/api/contact.html"}

    # Add an absolute $ref that matches the original base
    spec_doc["components"] = spec_doc.get("components", {})
    spec_doc["components"]["schemas"] = spec_doc["components"].get("schemas", {})
    spec_doc["components"]["schemas"]["TestSchema"] = {
        "$ref": "http://old.example.com/api/schemas/test.json"
    }

    # Now retarget from old base to new base with refs_only=True
    opts2 = RewriteOptions(
        base_url="https://new.example.com/v2/",
        original_base_url="http://old.example.com/api/",
        include_absolute_urls=True,
        refs_only=True,
    )
    changed = rewrite_urls_inplace(spec_doc, opts2)

    assert changed > 0, "Should have retargeted some absolute $ref URLs"

    # Verify that non-$ref URL fields were NOT retargeted
    assert spec_doc["info"]["termsOfService"] == "http://old.example.com/api/terms.html", (
        "Non-$ref URL fields should not be retargeted with refs_only=True"
    )
    assert spec_doc["info"]["contact"]["url"] == "http://old.example.com/api/contact.html", (
        "Non-$ref URL fields should not be retargeted with refs_only=True"
    )

    # Verify that the $ref was retargeted
    assert spec_doc["components"]["schemas"]["TestSchema"]["$ref"] == (
        "https://new.example.com/v2/schemas/test.json"
    ), "Absolute $ref URLs should be retargeted"
