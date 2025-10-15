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
