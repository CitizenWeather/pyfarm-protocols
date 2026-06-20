"""Load and validate GrowSpec protocols from YAML."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


class ProtocolLoader:
    """Load GrowSpec protocol files."""

    def __init__(self, protocols_dir: Optional[Path] = None):
        """Initialize protocol loader.

        Args:
            protocols_dir: Root directory containing protocols
                          (defaults to ./protocols relative to this file)
        """
        if protocols_dir is None:
            # Default to protocols/ directory at repo root
            this_dir = Path(__file__).parent.parent.parent.parent
            protocols_dir = this_dir / "protocols"

        self.protocols_dir = Path(protocols_dir)
        if not self.protocols_dir.exists():
            raise FileNotFoundError(f"Protocols directory not found: {self.protocols_dir}")

    def list_protocols(
        self,
        crop_type: Optional[str] = None,
    ) -> list[dict]:
        """List available protocols.

        Args:
            crop_type: Filter by crop type (mushroom, microgreen, etc.)

        Returns:
            List of protocol metadata dicts
        """
        protocols = []

        # Search for growspec.yaml files
        for spec_file in self.protocols_dir.rglob("growspec.yaml"):
            if spec_file.is_file():
                try:
                    spec = self.load_spec(spec_file)
                    if crop_type is None or spec.get("crop_type") == crop_type:
                        protocols.append(
                            {
                                "id": str(spec_file.parent),
                                "name": spec.get("name"),
                                "cultivar_id": spec.get("cultivar_id"),
                                "author": spec.get("author"),
                                "difficulty": spec.get("difficulty"),
                                "cycle_days": spec.get("cycle_days"),
                                "path": str(spec_file),
                            }
                        )
                except Exception:
                    # Skip invalid files
                    pass

        return sorted(protocols, key=lambda p: p["name"])

    def load_spec(self, spec_path: Path | str) -> dict:
        """Load a GrowSpec from file.

        Args:
            spec_path: Path to growspec.yaml or growspec.json

        Returns:
            Parsed GrowSpec dict
        """
        spec_path = Path(spec_path)
        if not spec_path.exists():
            raise FileNotFoundError(f"GrowSpec not found: {spec_path}")

        # Load YAML or JSON
        if spec_path.suffix == ".yaml" or spec_path.suffix == ".yml":
            if yaml is None:
                raise ImportError("PyYAML required for YAML loading: pip install pyyaml")
            with open(spec_path) as f:
                spec = yaml.safe_load(f)
        elif spec_path.suffix == ".json":
            with open(spec_path) as f:
                spec = json.load(f)
        else:
            raise ValueError(f"Unsupported format: {spec_path.suffix}")

        return spec or {}

    def validate_spec(self, spec: dict) -> tuple[bool, list[str]]:
        """Validate a GrowSpec dict.

        Args:
            spec: GrowSpec dict

        Returns:
            Tuple of (valid, list of error messages)
        """
        errors = []

        # Required fields
        required = ["name", "cultivar_id", "phases"]
        for field in required:
            if field not in spec:
                errors.append(f"Missing required field: {field}")

        # Validate phases
        phases = spec.get("phases", [])
        if not phases:
            errors.append("At least one phase required")

        total_days = 0
        for i, phase in enumerate(phases):
            if "name" not in phase:
                errors.append(f"Phase {i}: missing name")
            if "duration_days" not in phase:
                errors.append(f"Phase {i}: missing duration_days")
            else:
                duration = phase.get("duration_days", 0)
                if duration <= 0:
                    errors.append(f"Phase {i}: duration_days must be positive")
                total_days += duration

            # Check temperature range
            if "temperature" in phase:
                temp = phase["temperature"]
                if isinstance(temp, dict):
                    if "min" not in temp or "max" not in temp:
                        errors.append(f"Phase {i}: temperature must have min and max")

        # Warn if total cycle days doesn't match
        cycle_days = spec.get("cycle_days")
        if cycle_days and total_days != cycle_days:
            errors.append(
                f"Total phase days ({total_days}) doesn't match cycle_days ({cycle_days})"
            )

        return len(errors) == 0, errors

    def find_protocol(
        self,
        cultivar_id: str,
        crop_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Find a protocol by cultivar ID.

        Args:
            cultivar_id: Cultivar ID to search for
            crop_type: Optional crop type filter

        Returns:
            Protocol metadata dict or None
        """
        protocols = self.list_protocols(crop_type=crop_type)
        for proto in protocols:
            if proto["cultivar_id"] == cultivar_id:
                return proto
        return None
