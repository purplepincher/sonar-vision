# sonar-vision

Pure-Python toolkit for simulating active sonar pings and echoes, processing signals, tracking objects, and building 2-D occupancy maps.

> **Documentation:** [`PLUG_AND_PLAY.md`](./PLUG_AND_PLAY.md) · [`GETTING_STARTED.md`](./GETTING_STARTED.md) · [`ARCHITECTURE.md`](./ARCHITECTURE.md) · [`API_REFERENCE.md`](./API_REFERENCE.md) · [`LOW_LEVEL.md`](./LOW_LEVEL.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-blue?style=flat-square)](https://www.python.org/)

## Quickstart

Install from source into a virtual environment:

```bash
git clone https://github.com/purplepincher/sonar-vision.git
cd sonar-vision
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the tests:

```bash
pytest tests/
```

## Usage

### Simulate a sonar ping

```python
from sonar_vision import Sonar

sonar = Sonar(frequency=50000, max_range=500)
result = sonar.ping(distance=100)
print(f"Distance: {result.distance:.1f}m, SNR: {result.snr_db:.1f} dB")
```

Output:

```text
Distance: 99.1m, SNR: 38.0 dB
```

### Track objects across detections

```python
from sonar_vision import ObjectTracker, Detection

tracker = ObjectTracker()
tracker.update([Detection(x=10, y=20)])
tracker.update([Detection(x=12, y=22)])
tracker.update([Detection(x=14, y=19)])

print(f"Tracks: {len(tracker.tracks)}")
for t in tracker.tracks:
    print(f"  track {t.track_id}: ({t.x}, {t.y}), "
          f"speed {tracker.speed(t.track_id):.2f} m/s")
```

Output:

```text
Tracks: 1
  track 1: (14, 19), speed 5.13 m/s
```

### Generate and analyse a signal

```python
from sonar_vision import Signal

chirp = Signal.chirp(f0=1000, f1=5000, duration=0.01, sample_rate=44100)
print(f"Chirp samples: {chirp.n_samples}, "
      f"dominant freq: {chirp.dominant_frequency():.0f} Hz")
```

Output:

```text
Chirp samples: 441, dominant freq: 2950 Hz
```

### Build an occupancy map

```python
from sonar_vision import SpatialMap, Obstacle

m = SpatialMap(width=20, height=20, resolution=1.0)
m.add_obstacle(Obstacle(x=5, y=5, radius=1.0))
print(f"Occupied at (5,5): {m.is_occupied(5, 5)}")
print(f"Coverage: {m.coverage():.2%}")
```

Output:

```text
Occupied at (5,5): True
Coverage: 1.00%
```

## How it works

- **`Sonar`** models a single-beam active sonar. It computes round-trip time, applies two-way spreading and configurable absorption loss, adds target strength, and converts the resulting SNR into a detection probability and a noisy distance estimate.
- **`Signal`** provides discrete-time signal primitives: sine, noise, chirp, resampling, moving-average lowpass/highpass/bandpass filtering, thresholding, envelope, RMS/peak/energy metrics, and a naïve DFT magnitude.
- **`ObjectTracker`** uses greedy nearest-neighbour association with a constant-velocity prediction gate. Each track stores position and exponentially smoothed velocity; tracks time out after a configurable interval without updates.
- **`SpatialMap`** maintains a 2-D occupancy grid centred at the origin. Obstacles mark cells as occupied, free-space rays can mark cells as free, and ray casting returns the first occupied cell along a bearing.
- **`SonarDisplay`** renders ASCII visualisations: a polar radar sweep from
  bearing/distance readings, an occupancy-map downsample, and a tracker
  overlay showing active tracks and velocity vectors. No graphics
  dependencies — output is a plain string of characters.

## Configuration and options

### `Sonar`

```python
Sonar(
    sound_speed=1500.0,   # m/s
    frequency=50000.0,    # Hz
    pulse_duration=0.001, # seconds
    max_range=1000.0,     # meters
    beam_width=30.0,      # degrees
    source_level=200.0,   # arbitrary dB
    noise_level=60.0,     # arbitrary dB
)
```

Key methods: `ping(distance, target_strength=-20.0)`, `ping_return_signal(...)`, `round_trip_time(distance)`, `spreading_loss(distance)`, `absorption_loss(distance, absorption_db_km=10.0)`, `in_beam(bearing_offset_deg)`.

### `ObjectTracker`

```python
ObjectTracker(
    association_gate=5.0,  # meters
    max_velocity=10.0,     # m/s
    lost_timeout=5.0,      # seconds
)
```

Key methods: `update(detections)`, `predict(track_id, dt)`, `active_tracks()`, `prune_lost()`, `speed(track_id)`, `heading(track_id)`.

### `SpatialMap`

```python
SpatialMap(
    width=100.0,    # meters
    height=100.0,   # meters
    resolution=1.0, # meters per cell
)
```

Key methods: `add_obstacle(Obstacle(...))`, `get_cell(x, y)`, `set_cell(x, y, state)`, `ray_cast(ox, oy, angle_deg, max_dist)`, `mark_free_ray(...)`, `occupancy_count()`, `coverage()`.

### `SonarDisplay`

```python
SonarDisplay(
    width=41,      # characters
    height=21,     # characters
    range_m=50.0,  # meters represented by display radius
)
```

Key methods: `render_sweep(bearing_angles, distances, max_range=None)`,
`render_map(spatial_map)`, `render_tracks(tracker, cx_m=0, cy_m=0, now=None)`.

See [`API_REFERENCE.md`](./API_REFERENCE.md) for the full API.

## Limitations

- **Simulation only.** No hydrophone, audio device, or NMEA interface support.
- **Single-beam sonar.** No beamforming, phased arrays, or multi-beam reconstruction.
- **Simplified acoustics.** Propagation uses geometric spreading plus a constant dB/km absorption term; it is not a full ocean-acoustics solver.
- **No image or video processing.** The toolkit works with 1-D signals and 2-D positions, not camera frames.

## Capability verification

Every claim below was traced to working code and/or a passing test (86 tests,
all green under `pytest tests/`). Markers follow this org's convention:

- ✅ **real today** — traced to working code
- ⚠️ **real but conditional** — works, but needs something external or has caveats
- 🔮 **aspirational / later phase** — described as a direction, not implemented

### ✅ Real today

| Capability | Where in code |
|------------|---------------|
| Active sonar ping/echo simulation with two-way propagation loss | `sonar.py::ping`, `ping_return_signal` |
| Configurable sound speed, frequency, beam width, source/noise level | `sonar.py::Sonar` dataclass fields |
| Distance jitter proportional to range (stochastic estimate) | `sonar.py::ping` — `rng.gauss(0, 0.005 * distance)` |
| Signal primitives: sine, noise, chirp, resample | `signal.py::Signal` classmethods |
| Filters: lowpass, highpass, bandpass, threshold, envelope | `signal.py::Signal` — all tested in `TestSignalProcessing` |
| Analysis: rms, peak, energy, snr_db, dominant_frequency, dft_magnitude | `signal.py::Signal` — tested in `TestSignalAnalysis` |
| Signal arithmetic: `+` and `*` (scalar or signal) | `signal.py::Signal.__add__`, `__mul__` |
| Multi-object tracking: greedy nearest-neighbour association | `tracker.py::ObjectTracker.update` |
| Constant-velocity prediction with exponential smoothing (α=0.5) | `tracker.py::ObjectTracker._update_track` |
| Track lifecycle: active/lost/prune, predict, speed, heading | `tracker.py::ObjectTracker` — tested in `TestObjectTracker` |
| 2-D occupancy grid: obstacles, free-space rays, ray casting | `map.py::SpatialMap` — tested in `TestSpatialMap` |
| ASCII visualisation: radar sweep, map render, track overlay | `display.py::SonarDisplay` — tested in `TestSonarDisplay` |
| End-to-end pipeline: sonar → detect → track → map | `tests/test_simulation_scenarios.py` — 10 scenario tests |

### ⚠️ Real but conditional

| Capability | Condition |
|------------|-----------|
| DFT magnitude spectrum | ✅ Real, but it's a **naïve O(N²) implementation** — fine for educational use with small signals (≤ a few hundred samples), impractical for long signals. Not an FFT. |
| Dominant frequency estimate | ✅ Real, but uses **zero-crossing counting**, not a spectral peak. Approximate — the test allows ±30 Hz tolerance on a 100 Hz signal. |
| Absorption loss | ✅ Real, but uses a **constant dB/km coefficient** that does not vary with frequency. Real seawater absorption is strongly frequency-dependent; you must pass an appropriate `absorption_db_km` for your conditions. |
| `SOUND_SPEED_AIR` (343 m/s) | ✅ Defined in `sonar.py`, but **not exported** by `__init__.py` — import it from `sonar_vision.sonar` if you need it. |
| `sim_pipeline` sub-package | See below. |

### 🔮 Aspirational / later phase

| Claimed direction | Status |
|-------------------|--------|
| `sim_pipeline` — AUV fleet simulation, mission planning, physics | A nested sub-package exists at `sonar-vision/packages/pipeline/sim_pipeline/` with its own `pyproject.toml` and tests, but its tests **cannot be collected** (the import path `from sim_pipeline import …` fails unless the sub-package is installed separately). `AUVFleetSimulator.run_for()` is a no-op stub (`pass`); `FluxPhysics` is an empty class (`pass`). The CHANGELOG notes it was "never actually published" to PyPI. Treat it as scaffolding, not a working feature. |
| Kalman/particle-filter tracking | Not implemented. The tracker is constant-velocity only. (Documented honestly in `LOW_LEVEL.md`.) |
| Multi-beam / phased-array beamforming | Not implemented. Single-beam model only. |

## Testing

```bash
pytest tests/
```

The suite covers unit tests (`tests/test_all.py`) and end-to-end simulation scenarios (`tests/test_simulation_scenarios.py`); all pass under Python 3.10+.

## License

MIT. See [`LICENSE`](./LICENSE).
