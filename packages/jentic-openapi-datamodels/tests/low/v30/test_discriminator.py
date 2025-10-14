"""Tests for Discriminator model."""

from jentic.apitools.openapi.datamodels.low.v30.discriminator import Discriminator


class TestDiscriminator:
    """Tests for Discriminator model."""

    def test_init_empty(self):
        """Test creating empty discriminator."""
        disc = Discriminator()
        assert len(disc) == 0

    def test_init_with_property_name(self):
        """Test creating discriminator with propertyName."""
        disc = Discriminator({"propertyName": "petType"})
        assert disc.property_name == "petType"

    def test_init_with_mapping(self):
        """Test creating discriminator with mapping."""
        disc = Discriminator(
            {
                "propertyName": "petType",
                "mapping": {"dog": "#/components/schemas/Dog", "cat": "#/components/schemas/Cat"},
            }
        )
        assert disc.property_name == "petType"
        assert disc.mapping == {
            "dog": "#/components/schemas/Dog",
            "cat": "#/components/schemas/Cat",
        }

    def test_property_name_setter(self):
        """Test setting propertyName."""
        disc = Discriminator()
        disc.property_name = "animalType"
        assert disc.property_name == "animalType"
        assert disc["propertyName"] == "animalType"

    def test_property_name_setter_none(self):
        """Test setting propertyName to None removes it."""
        disc = Discriminator({"propertyName": "petType"})
        disc.property_name = None
        assert "propertyName" not in disc

    def test_mapping_setter(self):
        """Test setting mapping."""
        disc = Discriminator({"propertyName": "petType"})
        disc.mapping = {"bird": "#/components/schemas/Bird"}
        assert disc.mapping == {"bird": "#/components/schemas/Bird"}

    def test_mapping_setter_none(self):
        """Test setting mapping to None removes it."""
        disc = Discriminator(
            {"propertyName": "petType", "mapping": {"dog": "#/components/schemas/Dog"}}
        )
        disc.mapping = None
        assert "mapping" not in disc

    def test_mapping_default_empty_dict(self):
        """Test mapping returns empty dict when not set."""
        disc = Discriminator({"propertyName": "petType"})
        assert disc.mapping == {}

    def test_supports_extensions(self):
        """Test that Discriminator supports specification extensions."""
        disc = Discriminator({"propertyName": "petType", "x-custom": "value"})
        extensions = disc.get_extensions()
        assert extensions == {"x-custom": "value"}

    def test_to_mapping(self):
        """Test converting to mapping."""
        disc = Discriminator(
            {"propertyName": "petType", "mapping": {"dog": "#/components/schemas/Dog"}}
        )
        result = disc.to_mapping()
        assert result == {"propertyName": "petType", "mapping": {"dog": "#/components/schemas/Dog"}}

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"propertyName": "vehicleType", "mapping": {"car": "#/components/schemas/Car"}}
        disc = Discriminator.from_mapping(data)
        assert disc.property_name == "vehicleType"
        assert disc.mapping == {"car": "#/components/schemas/Car"}
