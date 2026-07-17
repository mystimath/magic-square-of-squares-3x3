"""Generate the publication figure directly from the validated JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "formulations_comparison" / "benchmarks"
OUTPUT = ROOT / "paper" / "formulations_comparison" / "figures"


def load_json(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def seconds_label(value: float) -> str:
    if value >= 10:
        return f"{value:.1f} s".replace(".", ",")
    if value >= 1:
        return f"{value:.3f} s".replace(".", ",")
    return f"{value:.3f} s".replace(".", ",")


def main() -> None:
    catalog = load_json("catalog_validation_r100000.json")
    adapters = load_json("shared_catalog_parametric_r100000.json")
    if not catalog["catalogs_equal"] or not adapters["all_classes_equal"]:
        raise RuntimeError("La figure exige des artefacts validés et concordants.")

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.8), constrained_layout=True)
    colors = ["#7A5195", "#2F9EAA", "#3B82C4", "#F28E2B", "#D45087", "#5A5A5A"]

    catalog_names = ["Quadratique", "Paramétrique"]
    catalog_values = [catalog["quadratic_seconds"], catalog["parametric_seconds"]]
    axes[0].barh(catalog_names, catalog_values, color=colors[:2], height=0.58)
    axes[0].set_xscale("log")
    axes[0].set_title("A. Génération du catalogue")
    axes[0].set_xlabel("Temps mural (secondes, échelle logarithmique)")
    for index, value in enumerate(catalog_values):
        axes[0].text(value * 1.12, index, seconds_label(value), va="center", fontweight="bold")
    axes[0].text(
        0.03,
        0.06,
        f"Même catalogue : {catalog['catalog_size_quadratic']:,} progressions\n"
        f"Facteur mesuré : {catalog['speedup']:.1f}×".replace(",", " ").replace(".", ","),
        transform=axes[0].transAxes,
        va="bottom",
        fontsize=8,
    )

    names = ["B1", "B2", "C", "D-probe"]
    medians = [adapters["summary"][name]["median_seconds"] for name in names]
    lower = [
        adapters["summary"][name]["median_seconds"]
        - adapters["summary"][name]["min_seconds"]
        for name in names
    ]
    upper = [
        adapters["summary"][name]["max_seconds"]
        - adapters["summary"][name]["median_seconds"]
        for name in names
    ]
    axes[1].barh(names, medians, color=colors[2:], height=0.58)
    axes[1].errorbar(
        medians,
        range(len(names)),
        xerr=[lower, upper],
        fmt="none",
        ecolor="#202020",
        elinewidth=1,
        capsize=3,
    )
    axes[1].set_xscale("log")
    axes[1].invert_yaxis()
    axes[1].set_title("B. Coût propre des adaptateurs")
    axes[1].set_xlabel("Médiane de 5 répétitions (secondes, échelle logarithmique)")
    for index, value in enumerate(medians):
        axes[1].text(value * 1.12, index, seconds_label(value), va="center", fontweight="bold")

    for axis in axes:
        axis.grid(axis="x", which="major", color="#D8D8D8", linewidth=0.8)
        axis.grid(axis="x", which="minor", color="#EEEEEE", linewidth=0.5)
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)
        axis.xaxis.set_minor_locator(LogLocator(base=10, subs=range(2, 10)))
        axis.xaxis.set_minor_formatter(NullFormatter())

    fig.suptitle("Benchmark confirmatoire à R = 100 000", fontsize=12, fontweight="bold")
    fig.text(
        0.5,
        -0.02,
        "CPython 3.11.15, 16 processeurs logiques. Les temps caractérisent cette implémentation.",
        ha="center",
        fontsize=8,
        color="#444444",
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUTPUT / "benchmark_r100000.svg"
    fig.savefig(svg_path, bbox_inches="tight")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines())
        + "\n",
        encoding="utf-8",
    )
    fig.savefig(OUTPUT / "benchmark_r100000.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
