"""Comprehensive test suite for sonar_vision."""

import math
import time

import pytest

from sonar_vision.signal import Signal
from sonar_vision.sonar import Sonar, PingResult, SOUND_SPEED_WATER
from sonar_vision.map import SpatialMap, Obstacle, CellState
from sonar_vision.tracker import ObjectTracker, Track, Detection
from sonar_vision.display import SonarDisplay


# ═══════════════════════════════════════════════════════════════════
# Signal tests
# ═══════════════════════════════════════════════════════════════════

class TestSignalConstructors:
    def test_sine_frequency(self):
        s = Signal.sine(1000, 0.01, sample_rate=10000)
        assert s.sample_rate == 10000
        assert s.n_samples == 100
        assert abs(s.dominant_frequency() - 1000) < 200  # rough

    def test_sine_amplitude(self):
        s = Signal.sine(440, 1.0, amplitude=0.5)
        assert s.peak() <= 0.5 + 1e-9

    def test_noise(self):
        n = Signal.noise(0.1, sample_rate=1000, seed=42)
        assert n.n_samples == 100
        assert n.rms() > 0

    def test_noise_deterministic_with_seed(self):
        a = Signal.noise(0.01, seed=123)
        b = Signal.noise(0.01, seed=123)
        assert a.samples == b.samples

    def test_chirp(self):
        c = Signal.chirp(100, 1000, 0.1, sample_rate=5000)
        assert c.n_samples == 500
        assert c.duration == pytest.approx(0.1, abs=1e-4)

    def test_empty_signal(self):
        s = Signal()
        assert s.n_samples == 0
        assert s.duration == 0.0
        assert s.rms() == 0.0
        assert s.peak() == 0.0


class TestSignalProperties:
    def test_duration(self):
        s = Signal(samples=[0.0] * 100, sample_rate=1000)
        assert s.duration == pytest.approx(0.1)

    def test_rms(self):
        s = Signal(samples=[1.0, -1.0, 1.0, -1.0], sample_rate=1)
        assert s.rms() == pytest.approx(1.0)

    def test_energy(self):
        s = Signal(samples=[2.0, 2.0], sample_rate=1)
        assert s.energy() == pytest.approx(8.0)


class TestSignalProcessing:
    def test_resample(self):
        s = Signal.sine(100, 1.0, sample_rate=1000)
        r = s.resample(500)
        assert r.sample_rate == 500
        assert r.n_samples == 500

    def test_resample_empty(self):
        s = Signal()
        r = s.resample(100)
        assert r.n_samples == 0

    def test_lowpass_smoothing(self):
        # DC signal should not change
        s = Signal(samples=[1.0] * 100, sample_rate=100)
        lp = s.lowpass(10)
        assert all(v == pytest.approx(1.0) for v in lp.samples)

    def test_highpass_removes_dc(self):
        s = Signal(samples=[1.0 + 0.01 * (i % 2) for i in range(100)], sample_rate=100)
        hp = s.highpass(10)
        # Mean should be near zero
        mean = sum(hp.samples) / len(hp.samples)
        assert abs(mean) < 0.1

    def test_bandpass(self):
        s = Signal.sine(440, 1.0, sample_rate=10000)
        bp = s.bandpass(200, 800)
        assert bp.n_samples == s.n_samples

    def test_threshold(self):
        s = Signal(samples=[0.1, 0.5, -0.1, -0.5], sample_rate=1)
        t = s.threshold(0.2)
        assert t.samples == [0.0, 0.5, 0.0, -0.5]

    def test_envelope(self):
        s = Signal.sine(1000, 0.01, sample_rate=10000, amplitude=1.0)
        env = s.envelope()
        assert env.n_samples == s.n_samples
        assert all(v >= 0 for v in env.samples)


class TestSignalAnalysis:
    def test_snr(self):
        sig = Signal(samples=[1.0] * 100, sample_rate=1)
        noise = Signal(samples=[0.1] * 100, sample_rate=1)
        snr = sig.snr_db(noise)
        assert snr > 0

    def test_snr_zero_noise(self):
        sig = Signal(samples=[1.0] * 10, sample_rate=1)
        noise = Signal(samples=[0.0] * 10, sample_rate=1)
        assert sig.snr_db(noise) == float("inf")

    def test_dominant_frequency(self):
        # 100 Hz at 10000 Hz sample rate
        s = Signal.sine(100, 1.0, sample_rate=10000)
        freq = s.dominant_frequency()
        assert abs(freq - 100) < 30

    def test_dft_magnitude(self):
        s = Signal.sine(100, 0.1, sample_rate=1000)
        mag = s.dft_magnitude(n=100)
        assert len(mag) == 51  # N/2 + 1
        assert all(v >= 0 for v in mag)
        # Peak should be near bin for 100 Hz
        bin_idx = int(100 * 100 / 1000)  # k = f * N / fs
        assert bin_idx < len(mag)
        assert mag[bin_idx] > 0.3


class TestSignalArithmetic:
    def test_add(self):
        a = Signal(samples=[1.0, 2.0], sample_rate=1)
        b = Signal(samples=[3.0, 4.0], sample_rate=1)
        c = a + b
        assert c.samples == [4.0, 6.0]

    def test_add_mismatched_rate(self):
        a = Signal(samples=[1.0], sample_rate=1)
        b = Signal(samples=[1.0], sample_rate=2)
        with pytest.raises(ValueError):
            a + b

    def test_mul_scalar(self):
        a = Signal(samples=[2.0, 3.0], sample_rate=1)
        b = a * 2.0
        assert b.samples == [4.0, 6.0]

    def test_mul_signal(self):
        a = Signal(samples=[2.0, 3.0], sample_rate=1)
        b = Signal(samples=[0.5, 2.0], sample_rate=1)
        c = a * b
        assert c.samples == [1.0, 6.0]


# ═══════════════════════════════════════════════════════════════════
# Sonar tests
# ═══════════════════════════════════════════════════════════════════

class TestSonar:
    def test_defaults(self):
        s = Sonar()
        assert s.sound_speed == SOUND_SPEED_WATER
        assert s.frequency == 50000.0

    def test_generate_ping(self):
        s = Sonar(frequency=1000, pulse_duration=0.01)
        ping = s.generate_ping(sample_rate=10000)
        assert ping.n_samples == 100
        assert ping.sample_rate == 10000

    def test_round_trip_time(self):
        s = Sonar(sound_speed=1500)
        rtt = s.round_trip_time(750)
        assert rtt == pytest.approx(1.0)

    def test_distance_from_time(self):
        s = Sonar(sound_speed=1500)
        d = s.distance_from_time(1.0)
        assert d == pytest.approx(750.0)

    def test_roundtrip_consistency(self):
        s = Sonar()
        d = 100.0
        assert s.distance_from_time(s.round_trip_time(d)) == pytest.approx(d)

    def test_spreading_loss(self):
        s = Sonar()
        assert s.spreading_loss(0) == 0.0
        loss_100 = s.spreading_loss(100)
        loss_1000 = s.spreading_loss(1000)
        assert loss_1000 > loss_100

    def test_absorption_loss(self):
        s = Sonar()
        loss = s.absorption_loss(1000, absorption_db_km=10)
        assert loss == pytest.approx(10.0)

    def test_total_loss(self):
        s = Sonar()
        total = s.total_loss(1000)
        spreading = s.spreading_loss(1000)
        absorption = s.absorption_loss(1000)
        assert total == pytest.approx(spreading + absorption)

    def test_ping_valid(self):
        s = Sonar(max_range=2000)
        result = s.ping(500)
        assert not math.isnan(result.distance)
        assert result.distance > 0
        assert result.travel_time > 0
        assert 0 <= result.signal_strength <= 1

    def test_ping_out_of_range(self):
        s = Sonar(max_range=100)
        result = s.ping(200)
        assert math.isnan(result.distance)

    def test_ping_negative(self):
        s = Sonar()
        result = s.ping(-10)
        assert math.isnan(result.distance)

    def test_ping_return_signal(self):
        s = Sonar(sound_speed=1500, pulse_duration=0.001, max_range=2000)
        sig = s.ping_return_signal(100, sample_rate=44100)
        assert sig.n_samples > 0
        # Should have tx pulse, silence, and echo
        assert sig.duration > s.round_trip_time(100)

    def test_ping_return_out_of_range(self):
        s = Sonar(max_range=100)
        sig = s.ping_return_signal(200)
        assert sig.n_samples == 0

    def test_in_beam(self):
        s = Sonar(beam_width=30)
        assert s.in_beam(0)
        assert s.in_beam(15)
        assert not s.in_beam(20)

    def test_beam_coverage(self):
        s = Sonar(beam_width=45)
        assert s.beam_coverage() == 45


# ═══════════════════════════════════════════════════════════════════
# SpatialMap tests
# ═══════════════════════════════════════════════════════════════════

class TestSpatialMap:
    def test_creation(self):
        m = SpatialMap(100, 100, 1.0)
        assert m.cols == 100
        assert m.rows == 100

    def test_get_set_cell(self):
        m = SpatialMap(10, 10, 1.0)
        m.set_cell(0, 0, CellState.FREE)
        assert m.get_cell(0, 0) == CellState.FREE

    def test_out_of_bounds(self):
        m = SpatialMap(10, 10, 1.0)
        assert m.get_cell(999, 999) == CellState.UNKNOWN

    def test_add_obstacle(self):
        m = SpatialMap(20, 20, 1.0)
        obs = Obstacle(x=5, y=5, radius=2)
        m.add_obstacle(obs)
        assert len(m.obstacles) == 1
        assert m.is_occupied(5, 5)

    def test_remove_obstacle(self):
        m = SpatialMap(20, 20, 1.0)
        m.add_obstacle(Obstacle(x=5, y=5))
        m.remove_obstacle(0)
        assert len(m.obstacles) == 0
        assert m.is_free(5, 5)

    def test_nearest_obstacle(self):
        m = SpatialMap(100, 100, 1.0)
        m.add_obstacle(Obstacle(x=10, y=10))
        m.add_obstacle(Obstacle(x=50, y=50))
        nearest = m.nearest_obstacle(12, 12)
        assert nearest is not None
        assert nearest.x == 10

    def test_obstacles_in_radius(self):
        m = SpatialMap(100, 100, 1.0)
        m.add_obstacle(Obstacle(x=5, y=5))
        m.add_obstacle(Obstacle(x=40, y=40))
        found = m.obstacles_in_radius(0, 0, 10)
        assert len(found) == 1
        assert found[0].x == 5

    def test_distance_to_nearest(self):
        m = SpatialMap(100, 100, 1.0)
        m.add_obstacle(Obstacle(x=10, y=0))
        assert m.distance_to_nearest(0, 0) == pytest.approx(10.0)

    def test_distance_to_nearest_empty(self):
        m = SpatialMap(100, 100, 1.0)
        assert m.distance_to_nearest(0, 0) == float("inf")

    def test_clear(self):
        m = SpatialMap(10, 10, 1.0)
        m.add_obstacle(Obstacle(x=0, y=0))
        m.clear()
        assert len(m.obstacles) == 0
        counts = m.occupancy_count()
        assert counts[CellState.UNKNOWN] == m.rows * m.cols

    def test_ray_cast_hit(self):
        m = SpatialMap(20, 20, 1.0)
        m.add_obstacle(Obstacle(x=10, y=0, radius=1))
        hit = m.ray_cast(0, 0, 0, 20)
        assert hit is not None

    def test_ray_cast_miss(self):
        m = SpatialMap(20, 20, 1.0)
        hit = m.ray_cast(0, 0, 0, 20)
        assert hit is None

    def test_occupancy_count(self):
        m = SpatialMap(10, 10, 1.0)
        counts = m.occupancy_count()
        assert counts[CellState.UNKNOWN] == 100
        assert counts[CellState.FREE] == 0
        assert counts[CellState.OCCUPIED] == 0

    def test_coverage(self):
        m = SpatialMap(10, 10, 1.0)
        assert m.coverage() == 0.0
        m.set_cell(0, 0, CellState.FREE)
        assert m.coverage() > 0

    def test_mark_free_ray(self):
        m = SpatialMap(20, 20, 1.0)
        m.mark_free_ray(0, 0, 0, 10)
        assert m.is_free(5, 0)

    def test_point_obstacle(self):
        m = SpatialMap(20, 20, 1.0)
        m.add_obstacle(Obstacle(x=5, y=5, radius=0))
        assert m.is_occupied(5, 5)


# ═══════════════════════════════════════════════════════════════════
# ObjectTracker tests
# ═══════════════════════════════════════════════════════════════════

class TestObjectTracker:
    def test_single_detection(self):
        t = ObjectTracker()
        ids = t.update([Detection(x=10, y=20, timestamp=1.0)])
        assert len(ids) == 1
        track = t.get_track(ids[0])
        assert track is not None
        assert track.x == 10
        assert track.y == 20

    def test_track_association(self):
        t = ObjectTracker(association_gate=5.0)
        ids1 = t.update([Detection(x=10, y=10, timestamp=1.0)])
        ids2 = t.update([Detection(x=11, y=11, timestamp=2.0)])
        assert ids1[0] == ids2[0]  # same track
        track = t.get_track(ids1[0])
        assert track.detections == 2

    def test_new_track_creation(self):
        t = ObjectTracker(association_gate=1.0)
        ids1 = t.update([Detection(x=0, y=0, timestamp=1.0)])
        ids2 = t.update([Detection(x=50, y=50, timestamp=2.0)])
        assert ids1[0] != ids2[0]  # different tracks

    def test_velocity_estimation(self):
        t = ObjectTracker(association_gate=15.0)
        t.update([Detection(x=0, y=0, timestamp=1.0)])
        t.update([Detection(x=10, y=0, timestamp=2.0)])
        track = t.tracks[0]
        assert track.vx > 0  # moving in +x

    def test_active_lost_tracks(self):
        t = ObjectTracker(lost_timeout=1.0)
        t.update([Detection(x=0, y=0, timestamp=100.0)])
        assert len(t.active_tracks(now=100.5)) == 1
        assert len(t.lost_tracks(now=102.0)) == 1

    def test_prune_lost(self):
        t = ObjectTracker(lost_timeout=1.0)
        t.update([Detection(x=0, y=0, timestamp=100.0)])
        pruned = t.prune_lost(now=102.0)
        assert pruned == 1
        assert len(t.tracks) == 0

    def test_predict(self):
        t = ObjectTracker(association_gate=15.0)
        ids = t.update([Detection(x=0, y=0, timestamp=1.0)])
        t.update([Detection(x=10, y=0, timestamp=2.0)])
        pos = t.predict(ids[0], 1.0)
        assert pos is not None
        assert pos[0] > 10  # predicted ahead

    def test_predict_all(self):
        t = ObjectTracker()
        t.update([Detection(x=0, y=0, timestamp=1.0)])
        preds = t.predict_all(1.0)
        assert len(preds) == 1

    def test_nearest_track(self):
        t = ObjectTracker()
        t.update([Detection(x=5, y=5, timestamp=1.0)])
        t.update([Detection(x=50, y=50, timestamp=1.0)])
        nearest = t.nearest_track(0, 0, now=1.0)
        assert nearest is not None
        assert nearest.x == 5

    def test_tracks_in_radius(self):
        t = ObjectTracker()
        t.update([Detection(x=5, y=5, timestamp=1.0)])
        t.update([Detection(x=50, y=50, timestamp=1.0)])
        found = t.tracks_in_radius(0, 0, 10, now=1.0)
        assert len(found) == 1

    def test_speed_heading(self):
        t = ObjectTracker(association_gate=15.0)
        ids = t.update([Detection(x=0, y=0, timestamp=1.0)])
        t.update([Detection(x=10, y=0, timestamp=2.0)])
        speed = t.speed(ids[0])
        heading = t.heading(ids[0])
        assert speed > 0
        assert abs(heading) < 10 or abs(heading - 360) < 10  # ~0° = east

    def test_remove_track(self):
        t = ObjectTracker()
        ids = t.update([Detection(x=0, y=0, timestamp=1.0)])
        t.remove_track(ids[0])
        assert len(t.tracks) == 0

    def test_multiple_detections(self):
        t = ObjectTracker(association_gate=1.0)
        dets = [Detection(x=float(i * 10), y=float(i * 10), timestamp=1.0) for i in range(5)]
        ids = t.update(dets)
        assert len(ids) == 5
        assert len(t.tracks) == 5

    def test_speed_nonexistent(self):
        t = ObjectTracker()
        assert t.speed(999) == 0.0

    def test_heading_nonexistent(self):
        t = ObjectTracker()
        assert t.heading(999) == 0.0


# ═══════════════════════════════════════════════════════════════════
# SonarDisplay tests
# ═══════════════════════════════════════════════════════════════════

class TestSonarDisplay:
    def test_render_sweep_empty(self):
        d = SonarDisplay(width=21, height=11)
        out = d.render_sweep([], [])
        lines = out.split("\n")
        assert len(lines) == 11
        assert len(lines[0]) == 21
        assert "+" in lines[5]  # centre marker

    def test_render_sweep_with_detection(self):
        d = SonarDisplay(width=21, height=11, range_m=100)
        out = d.render_sweep([0], [50])
        assert "+" in out  # centre present
        # Should have at least one non-space/dot character
        chars = set(c for c in out if c not in (" ", "\n", "·"))
        assert len(chars) > 0  # at least a detection blip

    def test_render_sweep_out_of_range(self):
        d = SonarDisplay(range_m=100)
        out = d.render_sweep([0], [200])
        # Detection beyond range, should just have grid
        assert "+" in out

    def test_render_map(self):
        m = SpatialMap(10, 10, 1.0)
        d = SonarDisplay(width=5, height=5)
        out = d.render_map(m)
        lines = out.split("\n")
        assert len(lines) == 5

    def test_render_map_with_obstacle(self):
        m = SpatialMap(10, 10, 1.0)
        m.add_obstacle(Obstacle(x=0, y=0, radius=1))
        d = SonarDisplay(width=5, height=5)
        out = d.render_map(m)
        assert "#" in out

    def test_render_tracks(self):
        t = ObjectTracker()
        t.update([Detection(x=10, y=10, timestamp=1.0)])
        d = SonarDisplay(width=21, height=11, range_m=50)
        out = d.render_tracks(t, cx_m=0, cy_m=0, now=1.0)
        assert "+" in out

    def test_render_tracks_empty(self):
        t = ObjectTracker()
        d = SonarDisplay(width=21, height=11)
        out = d.render_tracks(t)
        assert "+" in out
