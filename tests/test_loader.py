"""Tests for pyfarm-protocols ProtocolLoader."""

from pathlib import Path

import pytest

from pyfarm.protocols.loader import ProtocolLoader


@pytest.fixture
def loader():
    """Create a ProtocolLoader instance."""
    return ProtocolLoader()


class TestProtocolLoaderListProtocols:
    """Test ProtocolLoader.list_protocols()."""

    def test_list_protocols_returns_all(self, loader):
        protocols = loader.list_protocols()
        assert len(protocols) == 8
        assert all(isinstance(p, dict) for p in protocols)

    def test_list_protocols_has_required_fields(self, loader):
        protocols = loader.list_protocols()
        for protocol in protocols:
            assert "name" in protocol
            assert "cultivar_id" in protocol
            assert "author" in protocol
            assert "difficulty" in protocol
            assert "cycle_days" in protocol

    def test_list_mushroom_protocols(self, loader):
        protocols = loader.list_protocols(crop_type="mushroom")
        assert len(protocols) == 3
        for p in protocols:
            assert "oyster" in p["cultivar_id"] or "shiitake" in p["cultivar_id"] or "lions" in p["cultivar_id"]

    def test_list_microgreen_protocols(self, loader):
        protocols = loader.list_protocols(crop_type="microgreen")
        assert len(protocols) == 5
        cultivar_ids = {p["cultivar_id"] for p in protocols}
        assert "radish-microgreen" in cultivar_ids
        assert "broccoli-microgreen" in cultivar_ids
        assert "sunflower-microgreen" in cultivar_ids
        assert "pea-shoots-microgreen" in cultivar_ids
        assert "alfalfa-microgreen" in cultivar_ids

    def test_list_protocols_sorted_by_name(self, loader):
        protocols = loader.list_protocols()
        names = [p["name"] for p in protocols]
        assert names == sorted(names)


class TestProtocolLoaderLoadSpec:
    """Test ProtocolLoader.load_spec()."""

    def test_load_spec_yaml(self, loader):
        # Find a protocol file
        protocols = loader.list_protocols()
        spec_path = next(p["path"] for p in protocols if "radish" in p["cultivar_id"])

        spec = loader.load_spec(spec_path)
        assert isinstance(spec, dict)
        assert "name" in spec
        assert "cultivar_id" in spec
        assert "phases" in spec

    def test_load_spec_missing_file(self, loader):
        with pytest.raises(FileNotFoundError):
            loader.load_spec("/nonexistent/path/growspec.yaml")

    def test_load_spec_invalid_format(self, loader):
        with pytest.raises(ValueError, match="Unsupported format"):
            loader.load_spec(Path("/tmp/test.txt"))

    def test_load_spec_content_radish(self, loader):
        protocols = loader.list_protocols()
        spec_path = next(p["path"] for p in protocols if "radish" in p["cultivar_id"])
        spec = loader.load_spec(spec_path)

        assert spec["cultivar_id"] == "radish-microgreen"
        assert spec["cycle_days"] == 7
        assert len(spec["phases"]) == 2


class TestProtocolLoaderValidateSpec:
    """Test ProtocolLoader.validate_spec()."""

    def test_validate_valid_spec(self, loader):
        protocols = loader.list_protocols()
        spec_path = next(p["path"] for p in protocols if "radish" in p["cultivar_id"])
        spec = loader.load_spec(spec_path)

        valid, errors = loader.validate_spec(spec)
        assert valid is True
        assert len(errors) == 0

    def test_validate_missing_name(self, loader):
        spec = {
            "cultivar_id": "test",
            "phases": [{"name": "test", "duration_days": 5}]
        }
        valid, errors = loader.validate_spec(spec)
        assert valid is False
        assert any("name" in str(e).lower() for e in errors)

    def test_validate_missing_cultivar_id(self, loader):
        spec = {
            "name": "test",
            "phases": [{"name": "test", "duration_days": 5}]
        }
        valid, errors = loader.validate_spec(spec)
        assert valid is False
        assert any("cultivar_id" in str(e).lower() for e in errors)

    def test_validate_missing_phases(self, loader):
        spec = {
            "name": "test",
            "cultivar_id": "test"
        }
        valid, errors = loader.validate_spec(spec)
        assert valid is False
        assert any("phase" in str(e).lower() for e in errors)

    def test_validate_empty_phases(self, loader):
        spec = {
            "name": "test",
            "cultivar_id": "test",
            "phases": []
        }
        valid, errors = loader.validate_spec(spec)
        assert valid is False
        assert any("phase" in str(e).lower() for e in errors)

    def test_validate_phase_missing_duration(self, loader):
        spec = {
            "name": "test",
            "cultivar_id": "test",
            "phases": [{"name": "test"}]
        }
        valid, errors = loader.validate_spec(spec)
        assert valid is False
        assert any("duration" in str(e).lower() for e in errors)

    def test_validate_phase_negative_duration(self, loader):
        spec = {
            "name": "test",
            "cultivar_id": "test",
            "phases": [{"name": "test", "duration_days": -5}]
        }
        valid, errors = loader.validate_spec(spec)
        assert valid is False
        assert any("positive" in str(e).lower() for e in errors)

    def test_validate_cycle_days_mismatch(self, loader):
        spec = {
            "name": "test",
            "cultivar_id": "test",
            "cycle_days": 10,
            "phases": [
                {"name": "phase1", "duration_days": 5},
                {"name": "phase2", "duration_days": 3}
            ]
        }
        valid, errors = loader.validate_spec(spec)
        assert valid is False
        assert any("cycle_days" in str(e).lower() for e in errors)


class TestProtocolLoaderFindProtocol:
    """Test ProtocolLoader.find_protocol()."""

    def test_find_protocol_by_cultivar(self, loader):
        result = loader.find_protocol("radish-microgreen")
        assert result is not None
        assert result["cultivar_id"] == "radish-microgreen"

    def test_find_protocol_not_found(self, loader):
        result = loader.find_protocol("nonexistent-cultivar")
        assert result is None

    def test_find_mushroom_protocol(self, loader):
        result = loader.find_protocol("oyster-grey-strain-a", crop_type="mushroom")
        assert result is not None
        assert result["cultivar_id"] == "oyster-grey-strain-a"

    def test_find_all_microgreen_cultivars(self, loader):
        microgreen_cultivars = [
            "radish-microgreen",
            "broccoli-microgreen",
            "sunflower-microgreen",
            "pea-shoots-microgreen",
            "alfalfa-microgreen"
        ]
        for cultivar_id in microgreen_cultivars:
            result = loader.find_protocol(cultivar_id)
            assert result is not None, f"Protocol not found for {cultivar_id}"
            assert result["cultivar_id"] == cultivar_id


class TestProtocolLoaderIntegration:
    """Integration tests for ProtocolLoader."""

    def test_load_and_validate_all_protocols(self, loader):
        protocols = loader.list_protocols()
        for proto_meta in protocols:
            spec_path = proto_meta["path"]
            spec = loader.load_spec(spec_path)
            valid, errors = loader.validate_spec(spec)
            assert valid, f"Protocol {proto_meta['name']} is invalid: {errors}"

    def test_all_8_cultivars_have_protocols(self, loader):
        expected_cultivars = {
            "oyster-grey-strain-a",
            "shiitake-dark-oak",
            "lions-mane-standard",
            "radish-microgreen",
            "broccoli-microgreen",
            "sunflower-microgreen",
            "pea-shoots-microgreen",
            "alfalfa-microgreen"
        }
        protocols = loader.list_protocols()
        found_cultivars = {p["cultivar_id"] for p in protocols}
        assert found_cultivars == expected_cultivars
