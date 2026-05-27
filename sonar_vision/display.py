"""SonarDisplay — ASCII radar rendering for sonar data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from sonar_vision.map import SpatialMap, CellState, Obstacle
from sonar_vision.tracker import ObjectTracker, Track


# ASCII intensity ramp for signal strength / proximity
_RAMP = " .:-=+*#%@"
_RAMP_LEN = len(_RAMP)


@dataclass
class SonarDisplay:
    """ASCII-based sonar radar display.

    Renders a top-down polar or Cartesian view using characters.

    Attributes:
        width: Display width in characters.
        height: Display height in characters.
        range_m: Maximum display range in meters.
    """

    width: int = 41
    height: int = 21
    range_m: float = 50.0

    # ── radar sweep ───────────────────────────────────────────────

    def render_sweep(
        self,
        bearing_angles: list[float],
        distances: list[float],
        max_range: float | None = None,
    ) -> str:
        """Render a radar sweep from bearing/distance readings.

        Each (bearing, distance) pair places a blip on the display.
        """
        rng = max_range or self.range_m
        grid: list[list[str]] = [
            [" " for _ in range(self.width)] for _ in range(self.height)
        ]
        cx = self.width // 2
        cy = self.height // 2

        # Draw crosshairs
        for x in range(self.width):
            grid[cy][x] = "·" if grid[cy][x] == " " else grid[cy][x]
        for y in range(self.height):
            grid[y][cx] = "·" if grid[y][cx] == " " else grid[y][cx]

        # Range rings (25%, 50%, 75%)
        for frac in (0.25, 0.5, 0.75):
            r_cells = int(frac * min(cx, cy))
            for angle_deg in range(0, 360, 5):
                ar = math.radians(angle_deg)
                px = cx + int(r_cells * math.cos(ar))
                py = cy - int(r_cells * math.sin(ar))
                if 0 <= px < self.width and 0 <= py < self.height:
                    grid[py][px] = "·"

        # Centre marker (draw after range rings to avoid overwrite)
        grid[cy][cx] = "+"

        # Plot detections
        for bearing, dist in zip(bearing_angles, distances):
            if dist > rng or dist <= 0:
                continue
            ar = math.radians(bearing)
            r_norm = dist / rng
            px = cx + int(r_norm * cx * math.cos(ar))
            py = cy - int(r_norm * cy * math.sin(ar))
            if 0 <= px < self.width and 0 <= py < self.height:
                intensity = int((1.0 - r_norm) * (_RAMP_LEN - 1))
                intensity = max(0, min(_RAMP_LEN - 1, intensity))
                grid[py][px] = _RAMP[intensity]

        lines = ["".join(row) for row in grid]
        return "\n".join(lines)

    # ── occupancy map ─────────────────────────────────────────────

    def render_map(self, smap: SpatialMap) -> str:
        """Render a SpatialMap as ASCII."""
        symbols = {CellState.UNKNOWN: " ", CellState.FREE: ".", CellState.OCCUPIED: "#"}
        # Downsample map to display size
        row_scale = smap.rows / self.height
        col_scale = smap.cols / self.width

        lines: list[str] = []
        for dr in range(self.height):
            row_start = int(dr * row_scale)
            row_end = min(smap.rows, int((dr + 1) * row_scale))
            line_chars: list[str] = []
            for dc in range(self.width):
                col_start = int(dc * col_scale)
                col_end = min(smap.cols, int((dc + 1) * col_scale))
                # Pick most interesting cell in block
                cell = CellState.UNKNOWN
                for r in range(row_start, row_end):
                    for c in range(col_start, col_end):
                        s = smap._grid[r][c]
                        if s == CellState.OCCUPIED:
                            cell = s
                        elif s == CellState.FREE and cell == CellState.UNKNOWN:
                            cell = s
                line_chars.append(symbols[cell])
            lines.append("".join(line_chars))
        return "\n".join(lines)

    # ── tracker overlay ───────────────────────────────────────────

    def render_tracks(
        self,
        tracker: ObjectTracker,
        cx_m: float = 0.0,
        cy_m: float = 0.0,
        now: float | None = None,
    ) -> str:
        """Render active tracks relative to a centre point."""
        grid: list[list[str]] = [
            [" " for _ in range(self.width)] for _ in range(self.height)
        ]
        cx = self.width // 2
        cy = self.height // 2

        # Crosshairs
        for x in range(self.width):
            grid[cy][x] = "·"
        for y in range(self.height):
            grid[y][cx] = "·"
        grid[cy][cx] = "+"

        active = tracker.active_tracks(now)
        for t in active:
            dx = t.x - cx_m
            dy = t.y - cy_m
            px = cx + int(dx / self.range_m * cx)
            py = cy - int(dy / self.range_m * cy)
            if 0 <= px < self.width and 0 <= py < self.height:
                # Draw track marker and velocity vector
                marker = str(t.track_id % 10) if t.track_id < 10 else "*"
                grid[py][px] = marker
                # Velocity indicator
                vscale = self.range_m / (tracker.max_velocity or 1.0) * 2
                vx_px = int(t.vx * vscale / self.range_m * cx)
                vy_px = int(t.vy * vscale / self.range_m * cy)
                ex = px + vx_px
                ey = py - vy_px
                # Simple line
                steps = max(abs(ex - px), abs(ey - py), 1)
                for i in range(1, steps + 1):
                    lx = px + (ex - px) * i // steps
                    ly = py + (ey - py) * i // steps
                    if 0 <= lx < self.width and 0 <= ly < self.height and grid[ly][lx] == " ":
                        grid[ly][lx] = "~"

        return "\n".join("".join(row) for row in grid)
