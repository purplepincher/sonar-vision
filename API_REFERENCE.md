# API Reference — Sonar Vision

> *Public Python API. MSRV: Python 3.10+.*

---

## `Sonar`

```python
class Sonar(sound_speed=1500, frequency=50000, pulse_duration=0.001,
            max_range=1000, beam_width=30, source_level=200, noise_level=60)
```

Active sonar model.

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `generate_ping` | `(sample_rate=44100) -> Signal` | Generate transmit tone burst |
| `ping` | `(distance) -> PingResult` | Simulate full ping → echo cycle |
| `round_trip_time` | `(distance) -> float` | Compute 2-way travel time |
| `distance_from_time` | `(travel_time) -> float` | Estimate distance from RTT |
| `spreading_loss` | `(distance) -> float` | Geometric spreading loss (dB) |
| `absorption_loss` | `(distance) -> float` | Absorption loss (dB), Thorp model |
| `detect` | `(signal_strength) -> bool` | SNR threshold detection |

**PingResult:**
| Field | Type | Description |
|-------|------|-------------|
| `distance` | `float` | Estimated distance (m) |
| `travel_time` | `float` | Round-trip time (s) |
| `signal_strength` | `float` | Received amplitude (0–1) |
| `snr_db` | `float` | Signal-to-noise ratio (dB) |
| `frequency` | `float` | Ping frequency (Hz) |

---

## `Signal`

```python
class Signal(samples=[], sample_rate=44100.0)
```

Discrete-time signal.

**Constructors:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `sine` | `(freq, duration, sample_rate, amplitude)` | Sine wave |
| `noise` | `(duration, sample_rate, amplitude, seed)` | Uniform noise |
| `chirp` | `(f0, f1, duration, sample_rate, amplitude)` | Linear chirp |

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `filter_lowpass` | `(cutoff, order=4) -> Signal` | Butterworth lowpass |
| `filter_highpass` | `(cutoff, order=4) -> Signal` | Butterworth highpass |
| `fft` | `() -> (freqs, magnitudes)` | FFT analysis |
| `energy` | `() -> float` | RMS energy |
| `envelope` | `() -> Signal` | Hilbert envelope |

---

## `ObjectTracker`

```python
class ObjectTracker(gating_distance=5.0, timeout=5.0, max_tracks=50)
```

Multi-object tracker with constant-velocity prediction.

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `update` | `(detections, timestamp) -> None` | Update with new detections |
| `tracks` | `() -> List[Track]` | Current tracks |
| `predict_next` | `(dt) -> List[Track]` | Predict future positions |

**Track fields:** `track_id`, `x`, `y`, `vx`, `vy`, `last_seen`, `detections`, `label`

**Detection fields:** `x`, `y`, `timestamp`, `confidence`, `label`

---

## `SpatialMap`

```python
class SpatialMap(resolution=1.0, width=100, height=100)
```

Occupancy grid.

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `update` | `(x, y, occupied) -> None` | Update cell |
| `occupancy` | `(x, y) -> float` | Get cell value |
| `grid` | `() -> List[List[float]]` | Full occupancy grid |

## Minimum Supported Python Version

Python 3.10+
