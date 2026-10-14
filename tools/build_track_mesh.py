#!/usr/bin/env python3
"""Build a lightweight ribbon-road mesh from exported SWE1R spline CSV data.

This creates a *preview approximation*, not a complete extraction of the
original game's road surfaces. The selected route follows next1/next2 links,
then samples a Catmull-Rom curve and builds road + striped curbs. No commercial
assets are embedded in this repository.

Example:
  python3 tools/build_track_mesh.py data/demo_track_points.csv \
      --out-obj data/demo_track.obj --out-header source/track_mesh.generated.h
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Point:
    point_id: int
    x: float
    y: float
    z: float
    successors: tuple[int, ...]


@dataclass(frozen=True)
class Vertex:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Triangle:
    vertices: tuple[Vertex, Vertex, Vertex]
    color: tuple[int, int, int]
    group: str


class TrackMeshError(ValueError):
    pass


def _finite_float(row: dict[str, str], key: str, line: int) -> float:
    try:
        value = float(row[key])
    except (KeyError, ValueError, TypeError) as exc:
        raise TrackMeshError(f"CSV line {line}: missing or invalid {key!r}") from exc
    if not math.isfinite(value):
        raise TrackMeshError(f"CSV line {line}: {key!r} must be finite")
    return value


def load_points(path: Path, scale: float = 1.0, up_axis: str = "y") -> dict[int, Point]:
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise TrackMeshError(f"cannot read {path}: {exc}") from exc
    if up_axis not in ("y", "z"):
        raise TrackMeshError("up-axis must be y or z")
    points: dict[int, Point] = {}
    with handle:
        reader = csv.DictReader(handle)
        required = {"point_id", "x", "y", "z", "next1", "next2", "next_count"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            missing = sorted(required - set(reader.fieldnames or []))
            raise TrackMeshError(f"CSV is missing required columns: {', '.join(missing)}")
        for line, row in enumerate(reader, 2):
            try:
                point_id = int(row["point_id"])
                next_count = max(0, min(2, int(row["next_count"])))
                raw_nexts = [int(row["next1"]), int(row["next2"])][:next_count]
            except (ValueError, TypeError) as exc:
                raise TrackMeshError(f"CSV line {line}: invalid point/link integer") from exc
            if point_id < 0 or point_id in points:
                raise TrackMeshError(f"CSV line {line}: negative or duplicate point_id {point_id}")
            raw_xyz = [_finite_float(row, axis, line) for axis in ("x", "y", "z")]
            # Renderer uses Y-up. If the source is Z-up, swap source Y/Z.
            xyz = ([raw_xyz[0], raw_xyz[1], raw_xyz[2]] if up_axis == "y"
                   else [raw_xyz[0], raw_xyz[2], raw_xyz[1]])
            xyz = [value * scale for value in xyz]
            successors = tuple(n for n in raw_nexts if n >= 0 and n != 0xFFFF)
            points[point_id] = Point(point_id, *xyz, successors)
    if len(points) < 3:
        raise TrackMeshError("at least three control points are required")
    known_ids = set(points)
    points = {pid: Point(p.point_id, p.x, p.y, p.z,
                         tuple(n for n in p.successors if n in known_ids and n != pid))
              for pid, p in points.items()}
    return points


def _distance_sq(a: Point, b: Point) -> float:
    return (a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2


def order_route(points: dict[int, Point], start_id: int | None = None) -> tuple[list[Point], bool]:
    """Follow successor links; at a branch prefer the least sharp turn."""
    if start_id is None:
        indegree = {pid: 0 for pid in points}
        for point in points.values():
            for target in point.successors:
                indegree[target] += 1
        starts = [pid for pid, degree in indegree.items() if degree == 0]
        start_id = min(starts) if starts else min(points)
    if start_id not in points:
        raise TrackMeshError(f"start point {start_id} is not in the CSV")

    route = [points[start_id]]
    visited = {start_id}
    closed = False
    previous_direction: tuple[float, float, float] | None = None
    while len(route) < len(points):
        current = route[-1]
        candidates = [points[n] for n in current.successors]
        if not candidates:
            break
        if start_id in [p.point_id for p in candidates]:
            closed = True
            break
        candidates = [p for p in candidates if p.point_id not in visited]
        if not candidates:
            break
        if previous_direction is None:
            nxt = min(candidates, key=lambda p: p.point_id)
        else:
            dx, dy, dz = previous_direction
            dlen = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
            def alignment(candidate: Point) -> tuple[float, int]:
                vx, vy, vz = candidate.x-current.x, candidate.y-current.y, candidate.z-current.z
                vlen = math.sqrt(vx*vx+vy*vy+vz*vz) or 1.0
                dot = (dx*vx+dy*vy+dz*vz)/(dlen*vlen)
                return (dot, -candidate.point_id)
            nxt = max(candidates, key=alignment)
        previous_direction = (nxt.x-current.x, nxt.y-current.y, nxt.z-current.z)
        route.append(nxt)
        visited.add(nxt.point_id)
    if start_id in route[-1].successors:
        closed = True
    if len(route) < 3:
        raise TrackMeshError(f"route from point {start_id} contains only {len(route)} points")
    return route, closed


def catmull_rom(route: list[Point], closed: bool, samples_per_segment: int) -> list[Vertex]:
    def at(index: int) -> Point:
        if closed:
            return route[index % len(route)]
        return route[min(len(route)-1, max(0, index))]

    samples: list[Vertex] = []
    segment_count = len(route) if closed else len(route) - 1
    for i in range(segment_count):
        p0, p1, p2, p3 = at(i-1), at(i), at(i+1), at(i+2)
        for j in range(samples_per_segment):
            t = j / samples_per_segment
            t2, t3 = t*t, t*t*t
            def curve(a: float, b: float, c: float, d: float) -> float:
                return 0.5 * ((2*b) + (-a+c)*t + (2*a-5*b+4*c-d)*t2 + (-a+3*b-3*c+d)*t3)
            samples.append(Vertex(curve(p0.x,p1.x,p2.x,p3.x),
                                  curve(p0.y,p1.y,p2.y,p3.y),
                                  curve(p0.z,p1.z,p2.z,p3.z)))
    if not closed:
        p = route[-1]
        samples.append(Vertex(p.x, p.y, p.z))
    if len(samples) < 3:
        raise TrackMeshError("smoothing produced too few samples")
    return samples


def road_boundaries(samples: list[Vertex], closed: bool, width: float) -> list[tuple[Vertex, Vertex]]:
    """Return left/right road-edge points from the same horizontal normals as the mesh."""
    half = width / 2.0
    boundaries: list[tuple[Vertex, Vertex]] = []
    for i, point in enumerate(samples):
        if not closed and i == 0:
            prev, nxt = samples[0], samples[1]
        elif not closed and i == len(samples) - 1:
            prev, nxt = samples[-2], samples[-1]
        else:
            prev, nxt = samples[(i - 1) % len(samples)], samples[(i + 1) % len(samples)]
        dx, dz = nxt.x - prev.x, nxt.z - prev.z
        length = math.hypot(dx, dz)
        if length < 1e-6:
            raise TrackMeshError(f"adjacent path samples collapse near sample {i}")
        nx, nz = dz / length, -dx / length
        boundaries.append((Vertex(point.x + nx * half, point.y + 0.15, point.z + nz * half),
                           Vertex(point.x - nx * half, point.y + 0.15, point.z - nz * half)))
    return boundaries


def write_boundaries_csv(path: Path, boundaries: list[tuple[Vertex, Vertex]], closed: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample_id", "left_x", "left_y", "left_z", "right_x", "right_y", "right_z", "closed_loop"])
        for index, (left, right) in enumerate(boundaries):
            writer.writerow([index, f"{left.x:.6f}", f"{left.y:.6f}", f"{left.z:.6f}",
                             f"{right.x:.6f}", f"{right.y:.6f}", f"{right.z:.6f}", int(closed)])


def write_collision_header(path: Path, boundaries: list[tuple[Vertex, Vertex]], closed: bool) -> None:
    """Emit a compact, asset-free boundary table for later off-road/collision integration."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "/* Generated by tools/build_track_mesh.py; estimated edges, not original collision data. */",
        "#ifndef SWE1R_TRACK_BOUNDARIES_GENERATED_H",
        "#define SWE1R_TRACK_BOUNDARIES_GENERATED_H",
        "typedef struct { float lx, ly, lz, rx, ry, rz; } RacerTrackBoundary;",
        "static const RacerTrackBoundary g_track_boundaries[] = {",
    ]
    for left, right in boundaries:
        values = (left.x, left.y, left.z, right.x, right.y, right.z)
        formatted = [f"{(0.0 if abs(value) < 0.0000005 else value):.5f}f" for value in values]
        lines.append("    {" + ", ".join(formatted) + "},")
    lines += [
        "};",
        "#define TRACK_BOUNDARY_COUNT ((unsigned int)(sizeof(g_track_boundaries) / sizeof(g_track_boundaries[0])))",
        f"#define TRACK_BOUNDARY_CLOSED {1 if closed else 0}",
        "#endif",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def make_mesh(samples: list[Vertex], closed: bool, width: float, curb_width: float) -> list[Triangle]:
    half = width / 2.0
    inner = half - curb_width * 0.20
    outer = half + curb_width
    # Share the exact same edge calculation with the collision-boundary exporters.
    sides = road_boundaries(samples, closed, width)

    triangles: list[Triangle] = []
    steps = len(samples) if closed else len(samples)-1
    road = (72, 74, 77)
    white, red = (220, 215, 194), (174, 47, 36)

    def add_quad(a0: Vertex, b0: Vertex, a1: Vertex, b1: Vertex,
                 color: tuple[int,int,int], group: str) -> None:
        triangles.append(Triangle((a0, b0, a1), color, group))
        triangles.append(Triangle((b0, b1, a1), color, group))

    def offset_pair(i: int, offset: float) -> tuple[Vertex, Vertex]:
        p = samples[i]
        if not closed and i == 0:
            prev, nxt = samples[0], samples[1]
        elif not closed and i == len(samples)-1:
            prev, nxt = samples[-2], samples[-1]
        else:
            prev = samples[(i-1) % len(samples)]
            nxt = samples[(i+1) % len(samples)]
        dx, dz = nxt.x-prev.x, nxt.z-prev.z
        length = math.hypot(dx, dz) or 1.0
        nx, nz = dz/length, -dx/length
        return (Vertex(p.x+nx*offset, p.y+0.19, p.z+nz*offset),
                Vertex(p.x-nx*offset, p.y+0.19, p.z-nz*offset))

    for i in range(steps):
        j = (i+1) % len(samples)
        left0, right0 = sides[i]
        left1, right1 = sides[j]
        add_quad(left0, right0, left1, right1, road, "road")
        inner0 = offset_pair(i, inner)
        inner1 = offset_pair(j, inner)
        outer0 = offset_pair(i, outer)
        outer1 = offset_pair(j, outer)
        curb_color = red if (i // 3) % 2 == 0 else white
        add_quad(inner0[0], outer0[0], inner1[0], outer1[0], curb_color, "curb_left")
        add_quad(inner0[1], outer0[1], inner1[1], outer1[1], curb_color, "curb_right")
    return triangles


def write_obj(path: Path, triangles: list[Triangle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Generated approximation of a spline ribbon road.",
             "# Control points + links are converted to a Catmull-Rom road mesh."]
    cursor = 1
    # Keep each material-like group contiguous so the OBJ is easy to inspect.
    for group_name in ("road", "curb_left", "curb_right"):
        lines.append(f"g {group_name}")
        for tri in triangles:
            if tri.group != group_name:
                continue
            for v in tri.vertices:
                lines.append(f"v {v.x:.7g} {v.y:.7g} {v.z:.7g}")
            lines.append(f"f {cursor} {cursor+1} {cursor+2}")
            cursor += 3
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_centerline_header(path: Path, samples: list[Vertex], closed: bool) -> None:
    """Write the smoothed route for the portable runtime physics module."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "/* Generated by tools/build_track_mesh.py. Do not hand-edit. */",
        "#ifndef SWE1R_TRACK_CENTERLINE_GENERATED_H",
        "#define SWE1R_TRACK_CENTERLINE_GENERATED_H",
        '#include "racer_physics.h"',
        "static const RacerTrackPoint g_track_centerline[] = {",
    ]
    for point in samples:
        def f(n: float) -> str:
            if abs(n) < 0.0000005:
                n = 0.0
            return f"{n:.5f}f"
        lines.append(f"    {{{f(point.x)}, {f(point.y)}, {f(point.z)}}},")
    lines += [
        "};",
        "#define TRACK_CENTERLINE_COUNT ((unsigned int)(sizeof(g_track_centerline) / sizeof(g_track_centerline[0])))",
        f"#define TRACK_CENTERLINE_CLOSED {1 if closed else 0}",
        "#endif",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_header(path: Path, triangles: list[Triangle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "/* Generated by tools/build_track_mesh.py. Do not hand-edit. */",
        "#ifndef SWE1R_TRACK_MESH_GENERATED_H",
        "#define SWE1R_TRACK_MESH_GENERATED_H",
        "#include <gccore.h>",
        "typedef struct { f32 x, y, z; u8 r, g, b; } TrackVertex;",
        "static const TrackVertex g_track_vertices[] = {",
    ]
    for tri in triangles:
        r, g, b = tri.color
        for v in tri.vertices:
            def f(n: float) -> str:
                if abs(n) < 0.0000005:
                    n = 0.0
                return f"{n:.5f}f"
            lines.append(f"    {{{f(v.x)}, {f(v.y)}, {f(v.z)}, {r}, {g}, {b}}},")
    lines += [
        "};",
        "#define TRACK_VERTEX_COUNT ((u16)(sizeof(g_track_vertices) / sizeof(g_track_vertices[0])))",
        "#endif",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build(csv_path: Path, out_obj: Path, out_header: Path, width: float,
          curb_width: float, samples_per_segment: int, scale: float,
          start_id: int | None, up_axis: str = "y",
          out_centerline: Path | None = None,
          out_boundaries_csv: Path | None = None,
          out_collision_header: Path | None = None) -> dict[str, int | bool]:
    if not math.isfinite(width) or width <= 0:
        raise TrackMeshError("road width must be a positive finite number")
    if not math.isfinite(curb_width) or curb_width <= 0 or curb_width >= width/2:
        raise TrackMeshError("curb width must be positive and less than half the road width")
    if not 1 <= samples_per_segment <= 64:
        raise TrackMeshError("samples per segment must be between 1 and 64")
    if not math.isfinite(scale) or scale <= 0:
        raise TrackMeshError("scale must be a positive finite number")
    points = load_points(csv_path, scale, up_axis)
    route, closed = order_route(points, start_id)
    samples = catmull_rom(route, closed, samples_per_segment)
    # Scale physical dimensions along with coordinates so the proportions persist.
    final_width = width * scale
    triangles = make_mesh(samples, closed, final_width, curb_width * scale)
    boundaries = road_boundaries(samples, closed, final_width)
    vertex_count = len(triangles) * 3
    if vertex_count > 65535:
        raise TrackMeshError(
            f"mesh needs {vertex_count} vertices; GX_Begin uses a 16-bit vertex count. "
            "Reduce --samples-per-segment or split the route into sections."
        )
    write_obj(out_obj, triangles)
    write_header(out_header, triangles)
    if out_centerline is not None:
        write_centerline_header(out_centerline, samples, closed)
    if out_boundaries_csv is not None:
        write_boundaries_csv(out_boundaries_csv, boundaries, closed)
    if out_collision_header is not None:
        write_collision_header(out_collision_header, boundaries, closed)
    return {"input_points": len(points), "route_points": len(route), "closed_loop": closed,
            "sampled_points": len(samples), "boundary_samples": len(boundaries),
            "triangles": len(triangles), "vertices": len(triangles)*3}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="CSV exported by tools/export_splines.py")
    parser.add_argument("--out-obj", type=Path, default=Path("track_mesh.obj"))
    parser.add_argument("--out-header", type=Path, default=Path("track_mesh.generated.h"))
    parser.add_argument("--out-centerline", type=Path, default=Path("source/track_centerline.generated.h"),
                        help="optional C header for racer physics centerline")
    parser.add_argument("--out-boundaries-csv", type=Path,
                        help="optional CSV containing estimated left/right road edges")
    parser.add_argument("--out-collision-header", type=Path,
                        help="optional C header containing estimated left/right road edges")
    parser.add_argument("--width", type=float, default=14.0, help="road width in source-coordinate units")
    parser.add_argument("--curb-width", type=float, default=1.2)
    parser.add_argument("--samples-per-segment", type=int, default=5)
    parser.add_argument("--scale", type=float, default=1.0, help="coordinate and dimension multiplier")
    parser.add_argument("--up-axis", choices=("y", "z"), default="y",
                        help="source vertical axis; output is always Y-up (default: y)")
    parser.add_argument("--start-point", type=int, help="start point ID (default: inferred from links)")
    args = parser.parse_args()
    try:
        stats = build(args.csv, args.out_obj, args.out_header, args.width,
                      args.curb_width, args.samples_per_segment, args.scale,
                      args.start_point, args.up_axis, args.out_centerline,
                      args.out_boundaries_csv, args.out_collision_header)
    except (OSError, TrackMeshError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("Track ribbon mesh generated:")
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ')}: {value}")
    print(f"  OBJ: {args.out_obj.resolve()}")
    print(f"  GX header: {args.out_header.resolve()}")
    if args.out_centerline:
        print(f"  Centerline header: {args.out_centerline.resolve()}")
    if args.out_boundaries_csv:
        print(f"  Road-edge CSV: {args.out_boundaries_csv.resolve()}")
    if args.out_collision_header:
        print(f"  Boundary header: {args.out_collision_header.resolve()}")
    print("Note: estimated road surface only; original model/texture/collision data is not reconstructed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
