from pathlib import Path
import argparse
import csv
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", required=True)
    parser.add_argument("--min-count", type=int, required=True)
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--max-total", type=int, required=True)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)

    if args.clean and dst.exists():
        shutil.rmtree(dst)

    dst.mkdir(parents=True, exist_ok=True)

    matched = 0
    kept_total = 0
    read_total = 0
    files_created = 0

    for path in sorted(src.glob("selected_shard_*.csv")):
        out_path = dst / path.name
        kept_in_file = 0

        with path.open(newline="", encoding="utf-8") as f_in:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames
            if not fieldnames:
                continue

            f_out = None
            writer = None

            for row in reader:
                read_total += 1
                count = int(row.get("count", 0))

                if count < args.min_count:
                    continue

                matched += 1

                if matched <= args.skip:
                    continue

                if kept_total >= args.max_total:
                    break

                if f_out is None:
                    f_out = out_path.open("w", newline="", encoding="utf-8")
                    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                    writer.writeheader()
                    files_created += 1

                writer.writerow(row)
                kept_in_file += 1
                kept_total += 1

            if f_out is not None:
                f_out.close()

        if kept_in_file == 0 and out_path.exists():
            out_path.unlink()

        if kept_total >= args.max_total:
            break

    print(f"Centres lus                  : {read_total:,}")
    print(f"Centres matchant min-count   : {matched:,}")
    print(f"Centres sautés               : {args.skip:,}")
    print(f"Centres conservés            : {kept_total:,}")
    print(f"Fichiers créés               : {files_created:,}")
    print(f"Dossier sortie               : {dst}")

if __name__ == "__main__":
    main()