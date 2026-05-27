"""SpatialMap — obstacle detection, mapping, and spatial queries."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CellState(Enum):
    """State of a grid cell."""
    UNKNOWN = 0
    FREE = 1
    OCCUPIED = 2


@dataclass
class Obstacle:
    """Detected obstacle.

    Attributes:
        x: X-coordinate in meters.
        y: Y-coordinate in meters.
        radius: Approximate radius in meters (0 for point obstacles).
        confidence: Detection confidence (0–1).
        label: Optional label.
    """

    x: float
    y: float
    radius: float = 0.0
    confidence: float = 1.0
    label: str = ""


@dataclass
class SpatialMap:
    """2-D occupancy grid map with obstacle management.

    The map covers a rectangular region centred at the origin.

    Attributes:
        width: Map width in meters.
        height: Map height in meters.
        resolution: Cell size in meters.
    """

    width: float = 100.0
    height: float = 100.0
    resolution: float = 1.0
    _obstacles: list[Obstacle] = field(default_factory=list)
    _grid: list[list[CellState]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        cols = max(1, int(self.width / self.resolution))
        rows = max(1, int(self.height / self.resolution))
        self._grid = [[CellState.UNKNOWN for _ in range(cols)] for _ in range(rows)]

    # ── grid helpers ──────────────────────────────────────────────

    @property
    def cols(self) -> int:
        return len(self._grid[0]) if self._grid else 0

    @property
    def rows(self) -> int:
        return len(self._grid)

    def _world_to_cell(self, x: float, y: float) -> tuple[int, int]:
        """Convert world coords to cell (row, col)."""
        col = int((x + self.width / 2.0) / self.resolution)
        row = int((y + self.height / 2.0) / self.resolution)
        return row, col

    def _cell_to_world(self, row: int, col: int) -> tuple[float, float]:
        """Convert cell (row, col) to world coords (centre of cell)."""
        x = (col + 0.5) * self.resolution - self.width / 2.0
        y = (row + 0.5) * self.resolution - self.height / 2.0
        return x, y

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    # ── cell access ───────────────────────────────────────────────

    def get_cell(self, x: float, y: float) -> CellState:
        """Get the state of the cell at world coordinates (x, y)."""
        row, col = self._world_to_cell(x, y)
        if not self._in_bounds(row, col):
            return CellState.UNKNOWN
        return self._grid[row][col]

    def set_cell(self, x: float, y: float, state: CellState) -> None:
        """Set the state of the cell at world coordinates (x, y)."""
        row, col = self._world_to_cell(x, y)
        if self._in_bounds(row, col):
            self._grid[row][col] = state

    # ── obstacles ─────────────────────────────────────────────────

    def add_obstacle(self, obstacle: Obstacle) -> None:
        """Add an obstacle and mark its cells as occupied."""
        self._obstacles.append(obstacle)
        # Mark cells within the obstacle radius (at least the center cell)
        cx, cy = obstacle.x, obstacle.y
        r_cells = max(1, int(math.ceil(obstacle.radius / self.resolution))) if obstacle.radius > 0 else 0
        center_row, center_col = self._world_to_cell(cx, cy)
        # Always mark the center cell
        if self._in_bounds(center_row, center_col):
            self._grid[center_row][center_col] = CellState.OCCUPIED
        for dr in range(-r_cells, r_cells + 1):
            for dc in range(-r_cells, r_cells + 1):
                nr, nc = center_row + dr, center_col + dc
                if self._in_bounds(nr, nc):
                    wx, wy = self._cell_to_world(nr, nc)
                    if obstacle.radius <= 0 or math.hypot(wx - cx, wy - cy) <= obstacle.radius:
                        self._grid[nr][nc] = CellState.OCCUPIED

    def remove_obstacle(self, index: int) -> None:
        """Remove obstacle by index and clear its cells."""
        if 0 <= index < len(self._obstacles):
            obs = self._obstacles.pop(index)
            self._mark_area_free(obs)

    def _mark_area_free(self, obs: Obstacle) -> None:
        r_cells = max(1, int(math.ceil(obs.radius / self.resolution))) if obs.radius > 0 else 1
        center_row, center_col = self._world_to_cell(obs.x, obs.y)
        for dr in range(-r_cells, r_cells + 1):
            for dc in range(-r_cells, r_cells + 1):
                nr, nc = center_row + dr, center_col + dc
                if self._in_bounds(nr, nc):
                    wx, wy = self._cell_to_world(nr, nc)
                    if obs.radius <= 0 or math.hypot(wx - obs.x, wy - obs.y) <= obs.radius:
                        self._grid[nr][nc] = CellState.FREE

    @property
    def obstacles(self) -> list[Obstacle]:
        return list(self._obstacles)

    def clear(self) -> None:
        """Clear all obstacles and reset grid."""
        self._obstacles.clear()
        for r in range(self.rows):
            for c in range(self.cols):
                self._grid[r][c] = CellState.UNKNOWN

    # ── queries ───────────────────────────────────────────────────

    def is_occupied(self, x: float, y: float) -> bool:
        """Check if position (x, y) is occupied."""
        return self.get_cell(x, y) == CellState.OCCUPIED

    def is_free(self, x: float, y: float) -> bool:
        """Check if position (x, y) is known free."""
        return self.get_cell(x, y) == CellState.FREE

    def nearest_obstacle(self, x: float, y: float) -> Optional[Obstacle]:
        """Return the nearest obstacle to (x, y), or None."""
        if not self._obstacles:
            return None
        return min(self._obstacles, key=lambda o: math.hypot(o.x - x, o.y - y))

    def obstacles_in_radius(self, x: float, y: float, radius: float) -> list[Obstacle]:
        """Return obstacles within *radius* meters of (x, y)."""
        return [o for o in self._obstacles if math.hypot(o.x - x, o.y - y) <= radius]

    def distance_to_nearest(self, x: float, y: float) -> float:
        """Distance to the nearest occupied cell or obstacle."""
        obs = self.nearest_obstacle(x, y)
        if obs is None:
            return float("inf")
        return math.hypot(obs.x - x, obs.y - y)

    # ── ray casting ───────────────────────────────────────────────

    def ray_cast(self, ox: float, oy: float, angle_deg: float, max_dist: float) -> Optional[tuple[float, float]]:
        """Cast a ray from (ox, oy) at *angle_deg* and return first hit (x, y) or None.

        Uses DDA-style stepping at cell resolution.
        """
        angle_rad = math.radians(angle_deg)
        dx = math.cos(angle_rad) * self.resolution * 0.5
        dy = math.sin(angle_rad) * self.resolution * 0.5
        steps = int(max_dist / (self.resolution * 0.5))
        cx, cy = ox, oy
        for _ in range(steps):
            if self.is_occupied(cx, cy):
                return (cx, cy)
            # Also check out of bounds
            row, col = self._world_to_cell(cx, cy)
            if not self._in_bounds(row, col):
                return None
            cx += dx
            cy += dy
        return None

    # ── statistics ────────────────────────────────────────────────

    def occupancy_count(self) -> dict[CellState, int]:
        """Count cells by state."""
        counts = {s: 0 for s in CellState}
        for row in self._grid:
            for cell in row:
                counts[cell] += 1
        return counts

    def coverage(self) -> float:
        """Fraction of map that is explored (FREE + OCCUPIED)."""
        total = self.rows * self.cols
        if total == 0:
            return 0.0
        counts = self.occupancy_count()
        explored = counts[CellState.FREE] + counts[CellState.OCCUPIED]
        return explored / total

    # ── mark free from sonar sweep ────────────────────────────────

    def mark_free_ray(self, ox: float, oy: float, angle_deg: float, distance: float) -> None:
        """Mark cells along a ray as FREE up to *distance* meters."""
        angle_rad = math.radians(angle_deg)
        steps = max(1, int(distance / self.resolution))
        for i in range(steps):
            t = (i + 0.5) * self.resolution
            if t > distance:
                break
            wx = ox + t * math.cos(angle_rad)
            wy = oy + t * math.sin(angle_rad)
            if self.get_cell(wx, wy) != CellState.OCCUPIED:
                self.set_cell(wx, wy, CellState.FREE)
