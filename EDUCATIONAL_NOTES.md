# Educational Notes — sonar-vision

This document explains the acoustic model behind `Sonar.ping()` at more
depth than the README allows. Every formula below was traced to the source
in `sonar_vision/sonar.py`.

## The active sonar equation (as implemented)

When you call `sonar.ping(distance)`, the library walks through a simplified
version of the active sonar equation. Here is the exact computation chain,
step by step:

### Step 1 — Round-trip time

```python
rtt = 2.0 * distance / sound_speed
```

Sound travels to the target and back, so the factor of 2 is load-bearing.
At the default `sound_speed=1500` m/s (water), a target at 750 m gives
`rtt = 1.0` s.

### Step 2 — Two-way transmission loss

```python
two_way_loss = 2.0 * (spreading_loss(distance) + absorption_loss(distance))
```

This is where the simplification lives. Real ocean acoustics uses complex
models (Rayleigh, normal modes, parabolic equation). This library uses two
terms:

- **Geometric spreading:** `20 * log10(distance)` dB. This is the
  *spherical* spreading law (20 log R). The code comment calls it
  "cylindrical + spherical" but the formula is pure spherical — there is
  no cylindrical (10 log R) component. For a real mixed-mode model you
  would switch from 20 log R to 10 log R beyond the transition range.
- **Absorption:** `absorption_db_km * distance / 1000` dB. A linear
  scaling with a constant coefficient. In reality, absorption is strongly
  frequency-dependent (Francois-Garrison formula), but here it's a flat
  `absorption_db_km` you pass in.

Both terms are doubled because the sound goes out *and* comes back.

### Step 3 — Received level and SNR

```python
received_level = source_level - two_way_loss + target_strength
snr = received_level - noise_level
```

`target_strength` (default -20 dB) is added because a reflective target
*returns* energy. The SNR is simply received level minus the ambient noise
floor.

### Step 4 — Detection probability (the sigmoid)

```python
strength = 1.0 / (1.0 + math.exp(-(snr - 6.0) / 3.0))
```

This is a logistic sigmoid centred at SNR = 6 dB with a steepness
controlled by the divisor 3.0. What it means in practice:

| SNR (dB) | Detection probability |
|----------|-----------------------|
| 0        | ~12%                  |
| 3        | ~27%                  |
| 6        | 50% (the crossover)   |
| 9        | ~73%                  |
| 12       | ~88%                  |
| 15       | ~95%                  |

So an SNR of ~6 dB is the "maybe I see it" threshold, and ~12 dB is
"confident detection." This is why the simulation scenario tests use
`DETECTION_THRESHOLD = 0.05` as a minimum `signal_strength` — that
corresponds to roughly SNR = -3 dB, a generous "anything above noise" bar.

### Step 5 — Distance jitter

```python
jitter = rng.gauss(0, 0.005 * distance)
estimated_distance = distance + jitter
```

The measurement noise is **proportional to range** — at 100 m the standard
deviation is 0.5 m, at 500 m it's 2.5 m. This models the fact that timing
errors translate to larger distance errors at longer ranges. Note that the
random number generator is **re-seeded on every call** (`random.Random()`
with no seed), so each ping produces a different jitter — there is no
deterministic mode for `ping()` itself.

## Why the tracker uses Euclidean gating (and what that means)

The `ObjectTracker` associates detections to tracks using a simple rule:
for each detection (sorted by confidence, highest first), find the nearest
predicted track position within `association_gate` meters. "Nearest" here
is **plain Euclidean distance** — `math.hypot(px - det.x, py - det.y)`.

This is a deliberate simplification. A Kalman filter would use Mahalanobis
distance (accounting for the predicted covariance — how uncertain we are
in each direction). Without a covariance matrix, Euclidean is the only
option, and it means:

- The gate is a **circle**, not an ellipse. A target moving fast along one
  axis has the same gate size as one moving slowly.
- The `association_gate` is in **meters of position error**, not in standard
  deviations. You tune it empirically: too small and you create duplicate
  tracks; too large and you merge distinct objects.
- The simulation tests use `association_gate=8.0` with targets moving at
  1-2 m/s over 1-second steps. That gives ~1-2 m of motion per step, well
  within the 8 m gate, so association is reliable. If your targets move
  faster or your update interval is longer, increase the gate.

## The velocity smoothing constant (α = 0.5)

When a track is updated, the new velocity is blended with the old:

```python
alpha = 0.5
track.vx = alpha * new_vx + (1.0 - alpha) * track.vx
```

An α of 0.5 means equal weight to the new measurement and the old estimate.
This is an **exponential moving average** — it smooths out noisy
measurements but also lags behind sudden direction changes. The trade-off:

- **Higher α** (e.g. 0.8): tracks sudden manoeuvres faster, but is noisier.
- **Lower α** (e.g. 0.2): smoother velocity estimates, but slower to react.

The constant is hardcoded at 0.5 and cannot be configured without
modifying `tracker.py`. This is worth knowing if your simulation has
targets that change direction frequently.
