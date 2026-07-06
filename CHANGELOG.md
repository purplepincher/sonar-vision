# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-07-06

First tagged release. Everything below happened before any version was
formally cut, folded into this one entry since it's the first.

### Added

- Core `sonar_vision` package: `Sonar` (ping/echo simulation), `Signal`
  (chirp/noise/filtering primitives), `ObjectTracker` (nearest-neighbor
  multi-target tracking), `SpatialMap` (2-D occupancy grid with ray
  casting).
- Standard documentation suite: `GETTING_STARTED.md`, `ARCHITECTURE.md`,
  `PLUG_AND_PLAY.md`, `API_REFERENCE.md`, `LOW_LEVEL.md`,
  `CONTRIBUTING.md`.
- End-to-end simulation scenario tests (`tests/test_simulation_scenarios.py`)
  covering realistic multi-target tracking with underwater acoustic
  parameters.
- A small, separate, undocumented sub-package
  (`sonar-vision/packages/pipeline/sim_pipeline`) with its own
  tag-triggered PyPI publish workflow — real code, never actually
  published (`sim-pipeline` returns 404 on PyPI as of this writing).
  Whether this ships as its own release is an open product decision,
  not resolved by this changelog entry.

### Fixed

- A real test-isolation bug: `TestCrossingTargets` was calling its
  `targets()` fixture method directly instead of letting pytest inject
  it, silently defeating the fixture's isolation.
- CI was masking failures with `pytest || true` (both the main suite and
  the pipeline sub-package's `ruff`/`mypy` checks) — removed the masking
  and fixed the one real lint failure it had been hiding (an unused
  `math` import in `sim_pipeline/__init__.py`).
- A travel-time assertion in the simulation tests that was checking the
  wrong arithmetic (`60/1500 = 0.04`, not `0.14`).

### Changed

- README rewritten from a narrative/promotional style to instructional:
  leads with Quickstart, real captured command output, explicit
  limitations section.
