# Sonar Vision — Signal Processing and Spatial Awareness for Agents

> **📚 Documentation:** [`PLUG_AND_PLAY.md`](./PLUG_AND_PLAY.md) · [`GETTING_STARTED.md`](./GETTING_STARTED.md) · [`ARCHITECTURE.md`](./ARCHITECTURE.md) · [`API_REFERENCE.md`](./API_REFERENCE.md) · [`LOW_LEVEL.md`](./LOW_LEVEL.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-blue?style=flat-square)](https://www.python.org/)

> High-fidelity underwater acoustic simulation and sonar analysis toolkit for Python. Simulate active sonar pings, process echo returns, track moving objects across detections, and build spatial maps from sonar data.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Overview](#api-overview)
- [License](#license)

---

## Overview

Sonar Vision is a pure-Python library for sonar-based perception in marine robotics and agent-based systems:

- **Sonar ping/echo simulation** — Spreading loss, absorption loss, noise
- **Signal generation and filtering** — Sine waves, chirps, noise, lowpass/highpass filters
- **Multi-object tracking** — Constant-velocity prediction with gating-based association
- **Spatial mapping** — Occupancy grids from sonar returns
- **Zero hardware required** — Pure Python, no special drivers or external dependencies

### Real-World Use Cases

1. **Marine robotics simulation** — Model sensor behavior before deploying hardware
2. **Multi-agent sonar fusion** — Combine detections from multiple autonomous vessels
3. **Training data generation** — Generate realistic sonar returns for ML model training

---

## Installation

```bash
pip install sonar-vision
```

**Requirements:** Python 3.10+

---

## Quick Start

```python
from sonar_vision import Sonar, ObjectTracker, Detection

# Create a sonar model
sonar = Sonar(frequency=50000, max_range=500)

# Ping a target at 100 meters
result = sonar.ping(distance=100)
print(f"Distance: {result.distance:.1f}m, SNR: {result.snr_db:.1f} dB")

# Track objects across multiple detections
tracker = ObjectTracker()
tracker.update([Detection(x=10, y=20)])
tracker.update([Detection(x=12, y=22)])
tracker.update([Detection(x=14, y=19)])
print(f"Tracks: {len(tracker.tracks)}")
```

---

## API Overview

### `Sonar`
Active sonar model. Configurable frequency, sound speed, beam width, source level, noise level.

| Method | Description |
|--------|-------------|
| `ping(distance)` | Simulate full ping → echo cycle |
| `generate_ping(sample_rate)` | Generate transmit tone burst |
| `round_trip_time(distance)` | Compute 2-way travel time |
| `spreading_loss(distance)` | Geometric spreading loss (dB) |
| `absorption_loss(distance)` | Thorp model absorption loss (dB) |

### `Signal`
Discrete-time signal processing. Constructors: `sine()`, `noise()`, `chirp()`. Filters: `filter_lowpass()`, `filter_highpass()`. Utilities: `fft()`, `energy()`, `envelope()`.

### `ObjectTracker`
Multi-object tracker with constant-velocity motion model. Gating-based association, timeout for lost tracks.

### `SpatialMap`
Occupancy grid from sonar returns. Resolution-configurable. `update(x, y, occupied)` and `grid()`.

---

## How It Fits

Sonar Vision is part of the [SuperInstance fleet](https://github.com/SuperInstance) ecosystem:

- **[cocapn-marine](https://github.com/SuperInstance/cocapn-marine)** — Marine sensor integration (NMEA 0183, PID autopilot)
- **[handy-marine-voice](https://github.com/SuperInstance/handy-marine-voice)** — Voice-controlled marine autopilot

---

## Testing

```bash
pip install pytest
pytest tests/
```

---

## License

MIT © SuperInstance Labs

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
