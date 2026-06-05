# LOW LEVEL — Sonar Vision

> *For contributors extending the sonar processing pipeline.*

## Internal Architecture

```
sonar-vision/
├── sonar_vision/
│   ├── __init__.py    # Package + re-exports (Sonar, Signal, etc.)
│   ├── signal.py      # Signal processing (generation, filtering, FFT)
│   ├── sonar.py       # Active sonar model (ping, propagation, detection)
│   ├── map.py         # Spatial occupancy grid
│   ├── tracker.py     # Multi-object tracking (gating, prediction)
│   └── display.py     # Visualization utilities
├── sonar-vision/      # Pipeline package (simulation pipeline)
├── tests/
│   └── test_all.py    # Integration tests
├── pyproject.toml
└── README.md
```

## Key Internal Patterns

### Spreading Loss Model
```python
# Cylindrical < 100m, spherical > 100m
if distance < 100:
    return 10 * math.log10(distance)  # cylindrical
else:
    return 20 * math.log10(distance)  # spherical
```

### Object Tracker Gating
Detections are associated to tracks using distance gating. A detection within `gating_distance` of a predicted track position is associated. Unassociated detections become new tracks. Tracks not updated within `timeout` seconds are removed.

### Constant-Velocity Prediction
```python
predicted_x = track.x + track.vx * dt
predicted_y = track.y + track.vy * dt
new_vx = track.vx * 0.9 + (dx / dt) * 0.1  # weighted update
new_vy = track.vy * 0.9 + (dy / dt) * 0.1
```

## Testing

```bash
pip install pytest
pytest tests/
```

Tests cover: ping simulation accuracy, signal generation, object tracking association, spatial map updates.

## Debugging

- Sonar prints signal strength and SNR for each ping
- Tracker logs track creation, association, and timeout
- Spatial map supports `grid()` for full inspection

## Future Work

- Kalman filter for improved tracking
- Multi-hypothesis tracking
- Underwater acoustic channel model
- Real-time NMEA depth sounder integration
