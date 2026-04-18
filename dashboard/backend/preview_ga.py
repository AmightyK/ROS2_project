#!/usr/bin/env python3
"""
Preview script for GA route calculation.
Called by the Rust backend via `python3 preview_ga.py <rooms> <mode>`.
Output format:
  route: [...]
  distance: <float>
"""

import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from ga_core import run_genetic_algorithm, load_distance_matrix, route_distance
except ImportError as e:
    print(f"route: []\ndistance: 0.0", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("route: []\ndistance: 0.0")
        return

    raw_rooms = sys.argv[1].split(",")
    mode = sys.argv[2] if len(sys.argv) > 2 else "ga"

    # Normalize room names: "Phong_1" or "1" -> "Phong_1"
    rooms = []
    for r in raw_rooms:
        r = r.strip()
        if not r:
            continue
        if not r.startswith("Phong_"):
            r = f"Phong_{r}"
        rooms.append(r)

    if not rooms:
        print("route: []\ndistance: 0.0")
        return

    try:
        matrix = load_distance_matrix()
    except Exception:
        print("route: []\ndistance: 0.0")
        return

    if mode == "sequential":
        route = rooms
    else:
        route = run_genetic_algorithm(rooms, distance_matrix=matrix)

    distance = route_distance(route, matrix)

    # Print in parseable format
    print(f"route: {route}")
    print(f"distance: {distance}")


if __name__ == "__main__":
    main()
