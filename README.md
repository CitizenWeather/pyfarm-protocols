# pyfarm-protocols

Versioned, shareable grow recipe library built on the GrowSpec format — a package index for cultivation plans.

## Purpose

Community-driven recipe library. Low cost, high flywheel value for early adoption.

## Phase 1 Scope

- **File Format** — GrowSpec YAML/JSON (versioned schema)
- **Directory Structure** — `protocols/{crop_type}/{cultivar_name}/{version}/growspec.yaml`
- **Metadata** — Author, date, yield data, notes, tags (difficulty, system type)
- **CLI Integration** — `pyfarm protocol list`, `pyfarm protocol load`, `pyfarm protocol inspect`
- **Validation** — GrowSpec validator checks schema before use
- **Registry** — 3 mushroom + 2 microgreens protocols curated in-repo

## Phase 1 Example Protocols

- `protocols/mushroom/oyster-grey/v1/growspec.yaml`
- `protocols/mushroom/shiitake/v1/growspec.yaml`
- `protocols/mushroom/lions-mane/v1/growspec.yaml`
- `protocols/microgreens/radish/v1/growspec.yaml`
- `protocols/microgreens/broccoli/v1/growspec.yaml`

## Not in Phase 1

- Package registry / remote repositories (Phase 2+)
- Version conflict resolution
- User contributions / PR workflow (but design for it)

## Integration

- Queried by pyfarm-cli for `protocol` commands
- References cultivar IDs from pyfarm-crops
- Encodes phenophase workflows from pyfarm-mycology
