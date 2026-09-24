#!/usr/bin/env python3
"""Generate deterministic representative access-log data for the eval."""

from pathlib import Path

path = Path("access.log")
with path.open("w", encoding="utf-8") as handle:
    for index in range(500_000):
        status = 500 if index % 997 == 0 else (200 if index % 7 else 404)
        handle.write(f"10.0.{index % 255}.{(index * 7) % 255} - - [GET] /item/{index % 900} {status}\n")
