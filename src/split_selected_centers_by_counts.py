from pathlib import Path
import argparse
import csv
import shutil
from collections import Counter, defaultdict

def parse_thresholds(text):
    return sorted({int(x.strip()) for x in text.split(",") if x.strip()}, reverse=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst-root", required=True)
    parser.add_argument("--thresholds", default="64,48,40,36,32,24,20,16,12")
    parser.add_argument("--max-total-per-threshold", type=int, default=2_000_000)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    src = Path(args.src)
    dst_root = Path(args.dst_root)
    thresholds = parse_thresholds(args.thresholds)

    if args.clean and dst_root.exists():
        shutil.rmtree(dst_root)

    for t in thresholds:
        (dst_root / f"count{t}" / "selected_centers").mkdir(parents=True, exist_ok=True)

    hist = Counter()
    totals = defaultdict(int)
    files_created = defaultdict(int)
    total_rows = 0

    for path in sorted(src.glob("selected_shard_*.csv")):
        writers = {}
        files = {}

        with path.open(newline="", encoding="utf-8") as f_in:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames
            if not fieldnames:
                continue

            for row in reader:
                total_rows += 1
                count = int(row.get("count", 0))
                hist[count] += 1

                for t in thresholds:
                    if count < t:
                        continue
                    if totals[t] >= args.max_total_per_threshold:
                        continue

                    if t not in writers:
                        out_dir = dst_root / f"count{t}" / "selected_centers"
                        out_path = out_dir / path.name
                        f_out = out_path.open("w", newline="", encoding="utf-8")
                        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                        writer.writeheader()
                        writers[t] = writer
                        files[t] = f_out
                        files_created[t] += 1

                    writers[t].writerow(row)
                    totals[t] += 1

        for f_out in files.values():
            f_out.close()

    print(f"Centres lus : {total_rows:,}")
    print()
    print("Distribution par count :")
    for c in sorted(hist):
        print(f"  count={c:3d} : {hist[c]:,}")

    print()
    print("Cumul >= seuil :")
    running = 0
    for c in sorted(hist, reverse=True):
        running += hist[c]
        print(f"  count >= {c:3d} : {running:,}")

    print()
    print("Couches écrites :")
    for t in thresholds:
        cap = "  [CAP ATTEINT]" if totals[t] >= args.max_total_per_threshold else ""
        print(
            f"  count >= {t:3d} : {totals[t]:,} centres, "
            f"{files_created[t]:,} fichiers{cap}"
        )

if __name__ == "__main__":
    main()