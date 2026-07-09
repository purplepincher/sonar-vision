# Agent Interface — sonar-vision

> **Role:** Pure-Python sonar simulation, signal processing, tracking, and spatial mapping toolkit
> **Language:** Python 3.10+
> **No runtime dependencies** — standard library only

---

## What an Agent Can Do Here

### Primary Actions

| Action | Entry Point | Description |
|--------|-------------|-------------|
| Install | `pip install -e ".[dev]"` | Editable install with dev dependencies (pytest) |
| Run tests | `pytest tests/` | 86 unit + integration tests |
| Simulate sonar ping | `Sonar.ping(distance)` | Active sonar ping/echo with two-way propagation loss |
| Track objects | `ObjectTracker.update(detections)` | Greedy nearest-neighbour multi-target tracking |
| Build occupancy map | `SpatialMap` / `mark_free_ray` | 2-D occupancy grid with ray casting |
| Render ASCII display | `SonarDisplay.render_*` | Radar sweep, map, and track overlay as text |

### Python Module (`sonar_vision/`)

```bash
pip install -e ".[dev]"     # Install in dev mode
pytest tests/               # Run tests
```

```python
from sonar_vision import Sonar, Signal, ObjectTracker, Detection, SpatialMap, Obstacle, SonarDisplay
```

---

## What This Repo Is NOT

> ⚠️ An earlier version of this file described a TypeScript/npm CLI tool
> (`npx sonar-vision ping`), LLM API keys (`DEEPINFRA_API_KEY`,
> `OPENAI_API_KEY`), TypeScript imports (`import { physics, ping } from
> 'sonar-vision'`), Python functions (`acoustic_environment`,
> `sound_propagation`), a `.devcontainer/`, and inter-repo communication
> with `cocapn-marine` and `DeckBoss`. **None of that exists in this
> repository.** There is no `package.json`, no TypeScript code, no CLI entry
> point, no `.devcontainer/`, and no functions named `acoustic_environment`
> or `sound_propagation`. The description below reflects what the code
> actually contains.

---

## Package Exports

All public symbols are re-exported from `sonar_vision/__init__.py`:

```python
from sonar_vision import (
    Signal,           # Discrete-time signal: sine, chirp, noise, filters, DFT
    Sonar,            # Active sonar model: ping, propagation, beam geometry
    PingResult,       # Dataclass returned by Sonar.ping()
    SOUND_SPEED_WATER,# Constant: 1500.0 m/s
    SpatialMap,       # 2-D occupancy grid
    Obstacle,         # Dataclass: x, y, radius, confidence, label
    CellState,        # Enum: UNKNOWN, FREE, OCCUPIED
    ObjectTracker,    # Multi-object tracker
    Track,            # Dataclass: track_id, x, y, vx, vy, last_seen, detections, label
    Detection,        # Dataclass: x, y, timestamp, confidence, label
    SonarDisplay,     # ASCII visualisation: render_sweep, render_map, render_tracks
)
```

Note: `SOUND_SPEED_AIR` (343.0 m/s) is defined in `sonar_vision/sonar.py` but
**not** re-exported by `__init__.py`. Import it directly if needed:
`from sonar_vision.sonar import SOUND_SPEED_AIR`.

---

## How to Report Back Results

1. Run the test suite (`pytest tests/`) and verify all 86 tests pass.
2. Commit changes with a descriptive message.
3. Log observations to `memory/JOURNAL.md` if present.

---

## See Also

- [`README.md`](../README.md) — Quickstart and capability verification
- [`API_REFERENCE.md`](../API_REFERENCE.md) — Full method-level API
- [`ARCHITECTURE.md`](../ARCHITECTURE.md) — Design overview
- [`LOW_LEVEL.md`](../LOW_LEVEL.md) — Internal implementation details
