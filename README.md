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

See [`API_REFERENCE.md`](./API_REFERENCE.md) for the full API.

## Limitations

- **Simulation only.** No hydrophone, audio device, or NMEA interface support.
- **Single-beam sonar.** No beamforming, phased arrays, or multi-beam reconstruction.
- **Simplified acoustics.** Propagation uses geometric spreading plus a constant dB/km absorption term; it is not a full ocean-acoustics solver.
- **No image or video processing.** The toolkit works with 1-D signals and 2-D positions, not camera frames.
- **Not on PyPI.** Install from source for now.

## Testing

```bash
pytest tests/
```

Most tests pass; two scenario tests currently fail because a fixture is called directly rather than injected.

## License

MIT. See [`LICENSE`](./LICENSE).
