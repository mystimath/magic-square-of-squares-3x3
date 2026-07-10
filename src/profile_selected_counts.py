# src/profile_selected_counts.py

from pathlib import Path
import argparse
import csv
from collections import Counter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    args = parser.parse_args()

    src = Path(args.src)
    hist = Counter()
    total = 0
    files = 0
    max_count = 0

    for path in sorted(src.glob("selected_shard_*.csv")):
        files += 1
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                c = int(row.get("count", 0))
                hist[c] += 1
                total += 1
                if c > max_count:
                    max_count = c

    print(f"Fichiers lus     : {files:,}")
    print(f"Centres lus      : {total:,}")
    print(f"Count max        : {max_count:,}")
    print()
    print("Distribution par count :")
    for c in sorted(hist):
        print(f"  count={c:2d} : {hist[c]:,}")

    print()
    print("Cumul >= seuil :")
    running = 0
    for c in sorted(hist, reverse=True):
        running += hist[c]
        print(f"  count >= {c:2d} : {running:,}")

if __name__ == "__main__":
    main()