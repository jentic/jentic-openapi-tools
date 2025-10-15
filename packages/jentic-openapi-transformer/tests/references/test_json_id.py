"""Tests for set_or_replace_top_level_json_id function."""

from jentic.apitools.openapi.transformer.core.references import (
    set_or_replace_top_level_json_id,
)


class TestSetOrReplaceTopLevelJsonId:
    """Tests for set_or_replace_top_level_json_id function."""

    def test_create_id_openapi_31(self):
        """Test creating $id on OpenAPI 3.1 document."""
        doc = {"openapi": "3.1.0", "info": {"title": "Test", "version": "1.0.0"}}

        set_or_replace_top_level_json_id(doc, "https://example.com/api.json")

        # Should modify the document and return success indicator
        assert doc["$id"] == "https://example.com/api.json"

    def test_update_existing_id_openapi_31(self):
        """Test updating existing $id on OpenAPI 3.1 document."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "$id": "https://old.example.com/api.json",
        }

        set_or_replace_top_level_json_id(doc, "https://new.example.com/api.json")

        assert doc["$id"] == "https://new.example.com/api.json"

    def test_no_id_on_openapi_30_by_default(self):
        """Test that $id is not added to OpenAPI 3.0 by default."""
        doc = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        set_or_replace_top_level_json_id(doc, "https://example.com/api.json")

        assert "$id" not in doc

    def test_force_id_on_openapi_30(self):
        """Test forcing $id on OpenAPI 3.0 document."""
        doc = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        set_or_replace_top_level_json_id(doc, "https://example.com/api.json", force_on_30=True)

        assert doc["$id"] == "https://example.com/api.json"

    def test_non_dict_document(self):
        """Test with non-dictionary document."""
        doc = ["not", "a", "dict"]

        set_or_replace_top_level_json_id(doc, "https://example.com/api.json")

        # Should not modify non-dict documents
        assert doc == ["not", "a", "dict"]
