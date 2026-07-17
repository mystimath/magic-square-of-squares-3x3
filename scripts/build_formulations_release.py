"""Build the allowlisted standalone formulations-comparison release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


VERSION = "1.0.0"
PACKAGE_NAME = f"formulations-comparison-v{VERSION}"
ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TARGET = DIST / PACKAGE_NAME
TEMPLATES = ROOT / "release" / PACKAGE_NAME

MAPPINGS = {
    "release/formulations-comparison-v1.0.0/README.md": "README.md",
    "release/formulations-comparison-v1.0.0/CITATION.cff": "CITATION.cff",
    "release/formulations-comparison-v1.0.0/CHANGELOG.md": "CHANGELOG.md",
    "release/formulations-comparison-v1.0.0/RELEASE_NOTES.md": "RELEASE_NOTES.md",
    "release/formulations-comparison-v1.0.0/LICENSE": "LICENSE",
    "paper/formulations_comparison/comparaison_algorithmique_formulations_carre_magique_carres.md": "paper/comparaison_algorithmique_formulations_carre_magique_carres.md",
    "paper/formulations_comparison/references_notes.md": "paper/references_notes.md",
    "docs/13-j0-scope-and-vocabulary.md": "docs/mathematical_scope.md",
    "docs/14-j1-verified-repository-inventory.md": "docs/repository_inventory.md",
    "docs/15-j2-mathematical-equivalences.md": "docs/mathematical_equivalences.md",
    "docs/16-j3-validation-core.md": "docs/validation_core.md",
    "docs/17-j4-prototypes-a-b.md": "docs/prototypes_a_b.md",
    "docs/18-j5-geometric-feasibility-c.md": "docs/geometric_feasibility_c.md",
    "docs/19-j6-elliptic-feasibility-d.md": "docs/elliptic_feasibility_d.md",
    "docs/20-j6bis-elliptic-strategy-bremner.md": "docs/elliptic_strategy_bremner.md",
    "docs/21-j7-benchmark-pilot.md": "docs/benchmark_pilot.md",
    "docs/22-j8-confirmatory-benchmark.md": "docs/benchmark_confirmatory.md",
    "docs/23-j9-paper-report.md": "docs/paper_report.md",
    "docs/24-j10-final-publication-audit.md": "docs/final_publication_audit.md",
    "results/formulations_comparison/benchmarks/catalog_validation_r100000.json": "results/catalog_validation_r100000.json",
    "results/formulations_comparison/benchmarks/shared_catalog_parametric_r100000.json": "results/shared_catalog_parametric_r100000.json",
    "results/formulations_comparison/benchmarks/pilot_benchmarks.json": "results/pilot_benchmarks.json",
    "results/formulations_comparison/benchmarks/pilot_benchmarks.csv": "results/pilot_benchmarks.csv",
    "results/formulations_comparison/sage/e24_probe.json": "results/e24_probe.json",
    "scripts/plot_formulations_benchmarks.py": "scripts/plot_formulations_benchmarks.py",
    "paper/formulations_comparison/figures/benchmark_r100000.svg": "paper/figures/benchmark_r100000.svg",
    "paper/formulations_comparison/figures/benchmark_r100000.png": "paper/figures/benchmark_r100000.png",
}

EXPERIMENTS_ROOT = Path("experiments/formulations_comparison")
FIXED_ZIP_TIME = (2026, 7, 17, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_mappings() -> dict[str, str]:
    mappings = dict(MAPPINGS)
    base = ROOT / EXPERIMENTS_ROOT
    for source in sorted(base.rglob("*.py")):
        relative = source.relative_to(ROOT).as_posix()
        mappings[relative] = relative
    return mappings


def ensure_safe_target() -> None:
    resolved_dist = DIST.resolve()
    resolved_target = TARGET.resolve()
    if resolved_target.parent != resolved_dist or resolved_target.name != PACKAGE_NAME:
        raise RuntimeError(f"unsafe release target: {resolved_target}")


def run_tests() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "experiments/formulations_comparison/tests",
            "-q",
        ],
        cwd=ROOT,
        check=True,
    )


def copy_allowlist(mappings: dict[str, str]) -> list[dict]:
    records = []
    for source_text, release_text in sorted(mappings.items(), key=lambda item: item[1]):
        source = ROOT / source_text
        destination = TARGET / release_text
        if not source.is_file():
            raise FileNotFoundError(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        records.append(
            {
                "source": source_text,
                "path": release_text,
                "size": destination.stat().st_size,
                "sha256": sha256(destination),
            }
        )
    return records


def write_integrity_files(records: list[dict]) -> None:
    manifest = {
        "schema_version": 1,
        "package": PACKAGE_NAME,
        "version": VERSION,
        "status": "release",
        "allowlisted_files": records,
    }
    manifest_path = TARGET / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    checksum_records = records + [
        {
            "path": "MANIFEST.json",
            "sha256": sha256(manifest_path),
        }
    ]
    (TARGET / "SHA256SUMS").write_text(
        "".join(f"{row['sha256']}  {row['path']}\n" for row in checksum_records),
        encoding="ascii",
    )


def create_reproducible_zip() -> Path:
    archive = DIST / f"{PACKAGE_NAME}.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(item for item in TARGET.rglob("*") if item.is_file()):
            relative = Path(PACKAGE_NAME) / path.relative_to(TARGET)
            info = zipfile.ZipInfo(relative.as_posix(), FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, path.read_bytes(), compresslevel=9)
    return archive


def main() -> None:
    ensure_safe_target()
    run_tests()
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)
    records = copy_allowlist(source_mappings())
    write_integrity_files(records)
    archive = create_reproducible_zip()
    print(f"built: {TARGET}")
    print(f"archive: {archive}")
    print(f"files: {sum(1 for path in TARGET.rglob('*') if path.is_file())}")
    print(f"archive_sha256: {sha256(archive)}")


if __name__ == "__main__":
    main()
