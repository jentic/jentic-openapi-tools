"""Tests for SecurityRequirement model."""

from jentic.apitools.openapi.datamodels.low.v30.security_requirement import SecurityRequirement


class TestSecurityRequirement:
    """Tests for SecurityRequirement model."""

    def test_init_empty(self):
        """Test creating empty security requirement."""
        req = SecurityRequirement()
        assert len(req) == 0
        assert req.get_schemes() == []

    def test_init_with_single_scheme(self):
        """Test creating with single security scheme."""
        req = SecurityRequirement({"api_key": []})
        assert req["api_key"] == []
        assert req.get_schemes() == ["api_key"]

    def test_init_with_oauth2_scopes(self):
        """Test creating OAuth2 requirement with scopes."""
        req = SecurityRequirement({"oauth2": ["read:users", "write:users"]})
        assert req["oauth2"] == ["read:users", "write:users"]
        assert req.get_schemes() == ["oauth2"]

    def test_init_with_multiple_schemes(self):
        """Test creating with multiple security schemes."""
        req = SecurityRequirement({"api_key": [], "bearer": []})
        assert len(req) == 2
        assert "api_key" in req
        assert "bearer" in req
        schemes = req.get_schemes()
        assert "api_key" in schemes
        assert "bearer" in schemes

    def test_dict_access(self):
        """Test dictionary-style access."""
        req = SecurityRequirement()
        req["basic"] = []
        assert req["basic"] == []
        assert "basic" in req

    def test_getitem_returns_list(self):
        """Test that __getitem__ returns list type."""
        req = SecurityRequirement({"api_key": []})
        scopes = req["api_key"]
        assert isinstance(scopes, list)
        assert scopes == []

    def test_get_schemes(self):
        """Test get_schemes method."""
        req = SecurityRequirement({"scheme1": [], "scheme2": ["scope1", "scope2"], "scheme3": []})
        schemes = req.get_schemes()
        assert len(schemes) == 3
        assert "scheme1" in schemes
        assert "scheme2" in schemes
        assert "scheme3" in schemes

    def test_does_not_support_extensions(self):
        """Test that SecurityRequirement does not support extensions."""
        # x-* are treated as security scheme names, not extensions
        req = SecurityRequirement({"api_key": [], "x-custom-auth": []})
        extensions = req.get_extensions()
        assert extensions == {}
        # x-custom-auth should be a valid scheme name
        assert "x-custom-auth" in req
        assert req.get_schemes() == ["api_key", "x-custom-auth"]

    def test_to_mapping(self):
        """Test converting to mapping."""
        req = SecurityRequirement({"oauth2": ["read", "write"], "api_key": []})
        result = req.to_mapping()
        assert result == {"oauth2": ["read", "write"], "api_key": []}

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"bearer": [], "oauth2": ["admin"]}
        req = SecurityRequirement.from_mapping(data)
        assert req["bearer"] == []
        assert req["oauth2"] == ["admin"]

    def test_repr(self):
        """Test string representation."""
        req = SecurityRequirement({"api_key": []})
        repr_str = repr(req)
        assert "SecurityRequirement" in repr_str
        assert "1 field" in repr_str

    def test_empty_requirement_means_optional(self):
        """Test that empty security requirement object means optional security."""
        # An empty security requirement in a list means the operation can be accessed
        # without any authentication
        req = SecurityRequirement({})
        assert len(req) == 0
        assert req.get_schemes() == []
