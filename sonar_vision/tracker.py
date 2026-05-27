"""ObjectTracker — multi-object tracking with motion prediction."""

from __future__ import annotations

import math
import time as _time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    """A tracked object.

    Attributes:
        track_id: Unique integer ID.
        x: Current estimated X position (m).
        y: Current estimated Y position (m).
        vx: Estimated X velocity (m/s).
        vy: Estimated Y velocity (m/s).
        last_seen: Timestamp of last update.
        detections: Number of detections received.
        label: Optional semantic label.
    """

    track_id: int
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    last_seen: float = 0.0
    detections: int = 1
    label: str = ""


@dataclass
class Detection:
    """A single detection observation.

    Attributes:
        x: Measured X position (m).
        y: Measured Y position (m).
        timestamp: Observation time (epoch seconds). None means use current time.
        confidence: Detection confidence (0–1).
        label: Optional label.
    """

    x: float
    y: float
    timestamp: float | None = None
    confidence: float = 1.0
    label: str = ""


@dataclass
class ObjectTracker:
    """Simple multi-object tracker with nearest-neighbour association.

    Attributes:
        association_gate: Maximum distance for associating a detection
            with an existing track (meters).
        max_velocity: Assumed maximum object velocity (m/s) — used
            for gating and prediction clamping.
        lost_timeout: Seconds without detection before a track is
            considered lost.
        next_id: Counter for assigning track IDs.
    """

    association_gate: float = 5.0
    max_velocity: float = 10.0
    lost_timeout: float = 5.0
    next_id: int = 1
    _tracks: dict[int, Track] = field(default_factory=dict)

    # ── track management ──────────────────────────────────────────

    @property
    def tracks(self) -> list[Track]:
        """Return all active tracks."""
        return list(self._tracks.values())

    def get_track(self, track_id: int) -> Optional[Track]:
        return self._tracks.get(track_id)

    def active_tracks(self, now: float | None = None) -> list[Track]:
        """Return tracks that have been seen within *lost_timeout*."""
        now = now or _time.time()
        return [t for t in self._tracks.values() if (now - t.last_seen) <= self.lost_timeout]

    def lost_tracks(self, now: float | None = None) -> list[Track]:
        """Return tracks that have timed out."""
        now = now or _time.time()
        return [t for t in self._tracks.values() if (now - t.last_seen) > self.lost_timeout]

    def remove_track(self, track_id: int) -> None:
        self._tracks.pop(track_id, None)

    def prune_lost(self, now: float | None = None) -> int:
        """Remove all lost tracks. Returns count removed."""
        lost = self.lost_tracks(now)
        for t in lost:
            del self._tracks[t.track_id]
        return len(lost)

    # ── update ────────────────────────────────────────────────────

    def _create_track(self, det: Detection) -> Track:
        tid = self.next_id
        self.next_id += 1
        t = Track(
            track_id=tid,
            x=det.x,
            y=det.y,
            last_seen=det.timestamp,
            label=det.label,
        )
        self._tracks[tid] = t
        return t

    def _update_track(self, track: Track, det: Detection) -> None:
        dt = det.timestamp - track.last_seen
        if dt > 0:
            new_vx = (det.x - track.x) / dt
            new_vy = (det.y - track.y) / dt
            # Clamp velocity
            speed = math.hypot(new_vx, new_vy)
            if speed > self.max_velocity:
                scale = self.max_velocity / speed
                new_vx *= scale
                new_vy *= scale
            # Exponential smoothing on velocity
            alpha = 0.5
            track.vx = alpha * new_vx + (1.0 - alpha) * track.vx
            track.vy = alpha * new_vy + (1.0 - alpha) * track.vy
        track.x = det.x
        track.y = det.y
        track.last_seen = det.timestamp
        track.detections += 1

    def update(self, detections: list[Detection], now: float | None = None) -> list[int]:
        """Process a batch of detections.

        Returns list of track IDs that were updated or created.
        """
        now = now or _time.time()
        updated_ids: list[int] = []

        # Simple greedy nearest-neighbour association
        used_tracks: set[int] = set()
        # Sort detections by confidence descending for greedy matching
        sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)

        for det in sorted_dets:
            if det.timestamp is None:
                det.timestamp = now
            best_id: Optional[int] = None
            best_dist = self.association_gate
            for t in self._tracks.values():
                if t.track_id in used_tracks:
                    continue
                # Predict position
                dt = det.timestamp - t.last_seen
                px = t.x + t.vx * dt
                py = t.y + t.vy * dt
                d = math.hypot(px - det.x, py - det.y)
                if d < best_dist:
                    best_dist = d
                    best_id = t.track_id

            if best_id is not None:
                self._update_track(self._tracks[best_id], det)
                used_tracks.add(best_id)
                updated_ids.append(best_id)
            else:
                t = self._create_track(det)
                updated_ids.append(t.track_id)

        return updated_ids

    # ── prediction ────────────────────────────────────────────────

    def predict(self, track_id: int, dt: float) -> Optional[tuple[float, float]]:
        """Predict position of track *track_id* *dt* seconds into the future.

        Returns (x, y) or None if track doesn't exist.
        """
        t = self._tracks.get(track_id)
        if t is None:
            return None
        return (t.x + t.vx * dt, t.y + t.vy * dt)

    def predict_all(self, dt: float) -> dict[int, tuple[float, float]]:
        """Predict positions of all tracks *dt* seconds ahead."""
        return {
            tid: (t.x + t.vx * dt, t.y + t.vy * dt)
            for tid, t in self._tracks.items()
        }

    # ── queries ───────────────────────────────────────────────────

    def nearest_track(self, x: float, y: float, now: float | None = None) -> Optional[Track]:
        """Return the nearest active track to (x, y)."""
        active = self.active_tracks(now)
        if not active:
            return None
        return min(active, key=lambda t: math.hypot(t.x - x, t.y - y))

    def tracks_in_radius(self, x: float, y: float, radius: float, now: float | None = None) -> list[Track]:
        """Return active tracks within *radius* meters of (x, y)."""
        return [
            t for t in self.active_tracks(now)
            if math.hypot(t.x - x, t.y - y) <= radius
        ]

    def speed(self, track_id: int) -> float:
        """Speed of a track in m/s."""
        t = self._tracks.get(track_id)
        if t is None:
            return 0.0
        return math.hypot(t.vx, t.vy)

    def heading(self, track_id: int) -> float:
        """Heading of a track in degrees (0 = east, 90 = north)."""
        t = self._tracks.get(track_id)
        if t is None or (t.vx == 0 and t.vy == 0):
            return 0.0
        return math.degrees(math.atan2(t.vy, t.vx)) % 360.0
