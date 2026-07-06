"""Tests for sim_pipeline module."""

import pytest
from sim_pipeline import (
    compute_physics,
    SonarRayTracer,
    Waypoint,
    MissionPlanner,
    AUVFleetSimulator,
    FluxPhysics,
)


class TestComputePhysics:
    """Tests for compute_physics()."""

    def test_season_winter(self):
        result = compute_physics(depth=10.0, chl=2.0, season="winter", sediment="mud")
        assert result["temperature"] == 4.0
        assert result["depth"] == 10.0
        assert result["chl"] == 2.0
        assert result["season"] == "winter"
        assert result["sediment"] == "mud"
        assert result["attenuation"] == pytest.approx(0.1 * 2.0 + 0.01)

    def test_season_spring(self):
        result = compute_physics(depth=5.0, chl=5.0, season="spring")
        assert result["temperature"] == 12.0
        assert result["attenuation"] == pytest.approx(0.1 * 5.0 + 0.01)

    def test_season_summer_default(self):
        result = compute_physics(depth=20.0)
        assert result["temperature"] == 22.0
        assert result["season"] == "summer"

    def test_season_autumn(self):
        result = compute_physics(depth=15.0, chl=0.0, season="autumn")
        assert result["temperature"] == 14.0
        assert result["chl"] == 0.0
        assert result["attenuation"] == pytest.approx(0.01)

    def test_unknown_season_fallback(self):
        result = compute_physics(depth=10.0, season="unknown")
        assert result["temperature"] == 15.0
        assert result["season"] == "unknown"
        assert result["attenuation"] == pytest.approx(0.01)  # chl=0

    def test_chl_passthrough(self):
        result = compute_physics(depth=10.0, chl=3.14)
        assert result["chl"] == 3.14


class TestSonarRayTracer:
    """Tests for SonarRayTracer."""

    def test_compute_return(self):
        tracer = SonarRayTracer()
        depth = 50.0
        distance = 200.0
        frequency = 1000.0
        result = tracer.compute_return(depth, distance, frequency)
        total_distance = depth + distance
        expected_time = total_distance / 1500.0
        assert result["total_travel_time_s"] == pytest.approx(expected_time)
        assert result["depth"] == depth
        assert result["distance"] == distance
        assert result["frequency"] == frequency

    def test_zero_distance(self):
        tracer = SonarRayTracer()
        result = tracer.compute_return(depth=100.0, distance=0.0, frequency=500.0)
        assert result["total_travel_time_s"] == pytest.approx(100.0 / 1500.0)
        assert result["distance"] == 0.0


class TestWaypoint:
    """Tests for Waypoint."""

    def test_default_label(self):
        wp = Waypoint(x=1.0, y=2.0)
        assert wp.x == 1.0
        assert wp.y == 2.0
        assert wp.label == ""

    def test_custom_label(self):
        wp = Waypoint(x=10.0, y=20.0, label="test")
        assert wp.x == 10.0
        assert wp.y == 20.0
        assert wp.label == "test"


class TestMissionPlanner:
    """Tests for MissionPlanner.lawnmower()."""

    def test_simple_lawnmower(self):
        planner = MissionPlanner()
        mission = planner.lawnmower("sweep", width=10.0, height=20.0, spacing=5.0)
        waypoints = mission.waypoints
        # cols = max(1, int(10/5)) = max(1,2) = 2 → 4 waypoints
        assert len(waypoints) == 4

        # i=0: (x=0, y=0) start, (x=0, y=20) end
        assert waypoints[0].x == 0.0
        assert waypoints[0].y == 0.0
        assert waypoints[0].label == "sweep_0_start"
        assert waypoints[1].x == 0.0
        assert waypoints[1].y == 20.0
        assert waypoints[1].label == "sweep_0_end"

        # i=1: odd ⇒ start at (x=5, y=20), end at (x=5, y=0)
        assert waypoints[2].x == 5.0
        assert waypoints[2].y == 20.0
        assert waypoints[2].label == "sweep_1_start"
        assert waypoints[3].x == 5.0
        assert waypoints[3].y == 0.0
        assert waypoints[3].label == "sweep_1_end"

    def test_width_smaller_than_spacing(self):
        planner = MissionPlanner()
        mission = planner.lawnmower("small", width=3.0, height=10.0, spacing=10.0)
        waypoints = mission.waypoints
        # cols = max(1, int(3/10)=0) = 1 → 2 waypoints
        assert len(waypoints) == 2
        # i=0 only
        assert waypoints[0].x == 0.0
        assert waypoints[0].y == 0.0
        assert waypoints[0].label == "small_0_start"
        assert waypoints[1].x == 0.0
        assert waypoints[1].y == 10.0
        assert waypoints[1].label == "small_0_end"

    def test_width_zero(self):
        planner = MissionPlanner()
        mission = planner.lawnmower("zero", width=0.0, height=5.0, spacing=2.0)
        waypoints = mission.waypoints
        # cols = max(1, int(0/2)=0) = 1 → 2 waypoints
        assert len(waypoints) == 2
        assert waypoints[0].x == 0.0

    def test_many_columns(self):
        planner = MissionPlanner()
        mission = planner.lawnmower("long", width=20.0, height=30.0, spacing=5.0)
        waypoints = mission.waypoints
        # cols = max(1, int(20/5)=4) = 4 → 8 waypoints
        assert len(waypoints) == 8
        # Verify alternating pattern across columns
        for i in range(4):
            start_idx = i * 2
            end_idx = i * 2 + 1
            x = i * 5.0
            if i % 2 == 0:
                assert waypoints[start_idx].y == 0.0
                assert waypoints[end_idx].y == 30.0
            else:
                assert waypoints[start_idx].y == 30.0
                assert waypoints[end_idx].y == 0.0
            assert waypoints[start_idx].x == x
            assert waypoints[end_idx].x == x
            assert waypoints[start_idx].label == f"long_{i}_start"
            assert waypoints[end_idx].label == f"long_{i}_end"


class TestAUVFleetSimulator:
    """Tests for AUVFleetSimulator."""

    def test_spawn_fleet(self):
        physics = FluxPhysics()
        sim = AUVFleetSimulator(physics)
        sim.spawn_fleet(5)
        summary = sim.fleet_summary()
        assert summary["count"] == 5

    def test_spawn_fleet_zero(self):
        physics = FluxPhysics()
        sim = AUVFleetSimulator(physics)
        sim.spawn_fleet(0)
        assert sim.fleet_summary()["count"] == 0

    def test_spawn_fleet_large(self):
        physics = FluxPhysics()
        sim = AUVFleetSimulator(physics)
        sim.spawn_fleet(100)
        assert sim.fleet_summary()["count"] == 100

    def test_run_for_does_not_raise(self):
        physics = FluxPhysics()
        sim = AUVFleetSimulator(physics)
        sim.spawn_fleet(3)
        # run_for should not raise any exception
        sim.run_for(10.0)

    def test_fleet_summary_after_spawn(self):
        physics = FluxPhysics()
        sim = AUVFleetSimulator(physics)
        sim.spawn_fleet(2)
        summary = sim.fleet_summary()
        # verify dictionary structure
        assert isinstance(summary, dict)
        assert "count" in summary
