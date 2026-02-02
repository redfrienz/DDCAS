#!/usr/bin/env python3
import argparse
import csv
import math
from collections import defaultdict
import heapq
from pathlib import Path


def great_circle_km(lat1, lon1, lat2, lon2):
    # Haversine formula on a sphere
    r = 6371.0088  # mean Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def build_graph(csv_path: Path):
    graph = defaultdict(list)
    coords = {}

    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row["source_airport"].strip()
            dst = row["destination_airport"].strip()
            if not src or not dst:
                continue

            try:
                src_lat = float(row["source_latitude"])
                src_lon = float(row["source_longitude"])
                dst_lat = float(row["destination_latitude"])
                dst_lon = float(row["destination_longitude"])
            except (ValueError, TypeError):
                continue

            coords[src] = (src_lat, src_lon)
            coords[dst] = (dst_lat, dst_lon)

            dist = great_circle_km(src_lat, src_lon, dst_lat, dst_lon)
            graph[src].append((dst, dist))

    return graph, coords


def dijkstra(graph, start, goal):
    pq = [(0.0, start, None)]
    visited = {}
    prev = {}

    while pq:
        dist, node, parent = heapq.heappop(pq)
        if node in visited:
            continue
        visited[node] = dist
        prev[node] = parent

        if node == goal:
            break

        for nxt, w in graph.get(node, []):
            if nxt in visited:
                continue
            heapq.heappush(pq, (dist + w, nxt, node))

    if goal not in visited:
        return None, None

    # Reconstruct path
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    return path, visited[goal]


def main():
    parser = argparse.ArgumentParser(
        description="Compute shortest great-circle path between airports from routes_capitals_only.csv"
    )
    parser.add_argument("--source", required=True, help="IATA code of source airport (e.g., ICN)")
    parser.add_argument("--destination", required=True, help="IATA code of destination airport (e.g., NRT)")
    parser.add_argument(
        "--csv",
        default="routes_capitals_only.csv",
        help="Path to routes CSV (default: routes_capitals_only.csv)",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    graph, _ = build_graph(csv_path)

    src = args.source.strip().upper()
    dst = args.destination.strip().upper()

    if src not in graph:
        raise SystemExit(f"Source airport not found in graph: {src}")

    path, total_km = dijkstra(graph, src, dst)
    if path is None:
        raise SystemExit(f"No path found from {src} to {dst}")

    print(" -> ".join(path))
    print(f"Total distance: {total_km:.2f} km")


if __name__ == "__main__":
    main()
