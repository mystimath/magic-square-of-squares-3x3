# src/filter_selected_centers.py

from pathlib import Path
import argparse
import csv
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", required=True)
    parser.add_argument("--min-count", type=int, required=True)
    parser.add_argument("--max-total", type=int, default=3_000_000)
    args = parser.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)

    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    total_in = 0
    total_out = 0
    files_out = 0

    for path in sorted(src.glob("selected_shard_*.csv")):
        out_path = dst / path.name
        kept = 0

        with path.open(newline="", encoding="utf-8") as f_in, out_path.open("w", newline="", encoding="utf-8") as f_out:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames
            if not fieldnames:
                continue

            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                total_in += 1
                count = int(row.get("count", 0))
                if count < args.min_count:
                    continue

                writer.writerow(row)
                kept += 1
                total_out += 1

                if total_out >= args.max_total:
                    break

        if kept == 0:
            out_path.unlink(missing_ok=True)
        else:
            files_out += 1

        if total_out >= args.max_total:
            break

    print(f"Centres lus      : {total_in:,}")
    print(f"Centres conservés: {total_out:,}")
    print(f"Fichiers créés   : {files_out:,}")
    print(f"Dossier sortie   : {dst}")

    if total_out >= args.max_total:
        print("Arrêt : max-total atteint.")

if __name__ == "__main__":
    main()