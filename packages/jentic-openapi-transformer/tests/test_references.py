from pathlib import Path
from jentic_openapi_parser import OpenAPIParser, dump_json
from jentic_openapi_parser.uri import load_uri
from jentic_openapi_transformer import (
    find_relative_urls,
    rewrite_urls_inplace,
    set_or_replace_top_level_json_id,
    RewriteOptions,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi" / "references"


def test_references():
    """Test the comprehensive reference processing functionality."""
    spec_file = FIXTURES_DIR / "root-relative-refs.json"
    spec_uri = spec_file.as_uri()
    spec_text = load_uri(spec_uri, 300, 300)

    spec_doc = OpenAPIParser().parse(spec_text)

    # Test find_relative_urls
    rels = find_relative_urls(spec_doc)
    assert len(rels) > 0, "Should find relative URLs in the test fixture"

    print("Relative URLs found at:")
    for jp, key, val in rels:
        print(f"  - /{'/'.join(map(str, jp))} = {val}")
        # Verify that found URLs are actually relative
        assert not val.startswith("http://") and not val.startswith("https://"), (
            f"Found URL should be relative: {val}"
        )
        assert not val.startswith("#"), f"Fragment-only refs should not be included: {val}"

    # Test rewrite_urls_inplace
    original_count = len(rels)
    opts = RewriteOptions(
        base_url="http://localhost:8080/root-relative-refs.json",
        original_base_url="http://localhost:8080/root-relative-refs.json",
        include_absolute_urls=False,
    )
    changed = rewrite_urls_inplace(spec_doc, opts)

    assert changed > 0, "Should have rewritten some URLs"
    assert changed == original_count, (
        f"Should have rewritten all {original_count} relative URLs, but changed {changed}"
    )
    print(f"Rewrote {changed} field(s)")

    # Verify that URLs were actually rewritten to absolute
    new_rels = find_relative_urls(spec_doc)
    assert len(new_rels) == 0, "After rewriting, there should be no relative URLs left"

    spec_text = dump_json(spec_doc)
    print(f"Rewritten \n{spec_text[:500]}")

    # Verify the rewritten document contains absolute URLs
    assert "http://localhost:8080/" in spec_text, "Rewritten document should contain absolute URLs"

    # Test set_or_replace_top_level_json_id
    original_id = spec_doc.get("$id")
    set_or_replace_top_level_json_id(spec_doc, "http://localhost:8080/root-relative-refs.json")

    # Should set ID on OpenAPI 3.0 when forced (the fixture is 3.0.3)
    # But since forse_on_30 defaults to False, it won't be set
    if spec_doc.get("openapi", "").startswith("3.1"):
        assert spec_doc.get("$id") == "http://localhost:8080/root-relative-refs.json", (
            "Should set $id on OpenAPI 3.1"
        )
    elif spec_doc.get("openapi", "").startswith("3.0"):
        # Default behavior for 3.0 - no $id should be set
        assert "$id" not in spec_doc or spec_doc.get("$id") == original_id, (
            "Should not set $id on OpenAPI 3.0 by default"
        )

    print("Document ID handling completed")


def test_references_with_force_id_on_30():
    """Test setting $id on OpenAPI 3.0 documents when forced."""
    spec_file = FIXTURES_DIR / "root-relative-refs.json"
    spec_uri = spec_file.as_uri()
    spec_text = load_uri(spec_uri, 300, 300)

    spec_doc = OpenAPIParser().parse(spec_text)

    # Force $id on OpenAPI 3.0
    set_or_replace_top_level_json_id(
        spec_doc, "http://localhost:8080/root-relative-refs.json", forse_on_30=True
    )

    # Should now have $id set regardless of OpenAPI version
    assert spec_doc.get("$id") == "http://localhost:8080/root-relative-refs.json", (
        "Should force $id on OpenAPI 3.0 when requested"
    )


def test_references_retarget_absolute_urls():
    """Test retargeting absolute URLs from one base to another."""
    spec_file = FIXTURES_DIR / "root-relative-refs.json"
    spec_uri = spec_file.as_uri()
    spec_text = load_uri(spec_uri, 300, 300)

    spec_doc = OpenAPIParser().parse(spec_text)

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
    spec_text = dump_json(spec_doc)
    assert "https://new.example.com/v2/" in spec_text, "Document should contain retargeted URLs"
