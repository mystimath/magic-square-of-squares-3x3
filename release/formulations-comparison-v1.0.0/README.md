# Formulations comparison for the 3×3 magic square of squares

Version `1.0.0`.

This standalone research package compares four mathematical formulations of
the 3×3 magic square of distinct positive squares problem:

- A: direct search from three base squares;
- B: arithmetic progressions of three squares (center and difference indexes);
- C: equal-area rational right triangles;
- D: congruent-number elliptic curves.

The main paper is written in French:

`paper/comparaison_algorithmique_formulations_carre_magique_carres.md`

## Main result

At `R=100000`, the quadratic and primitive parametric generators produce the
same 122,640 progressions object by object. Their measured times are 607.693954
and 0.421561 seconds respectively, a factor of 1441.53 on the documented
machine. No 9/9 class is found in the explicitly bounded common domain. This is
not a proof of global non-existence.

## Current status of the problem

The peer-reviewed literature still treats order 3 as open. Rome and Yamagishi
proved existence for every order `n>=4` in 2025. A 2026 arXiv preprint by Hill
claims non-existence for order 3; the paper included here identifies an
unsupported coefficient-comparison step in its final argument and therefore
does not treat that claim as established. See `paper/references_notes.md` for
the source audit and precise references.

## Tests

From the package root:

```powershell
python -m unittest discover -s experiments\formulations_comparison\tests -v
```

## Confirmatory benchmark

```powershell
python experiments\formulations_comparison\benchmark_shared_catalog.py `
  --bound 100000 --repetitions 5 --catalog-engine parametric `
  --output results\shared_catalog_parametric_r100000.json
```

The command recomputes the benchmark and may overwrite the copied result if the
same output path is selected. Timings are implementation- and machine-specific.

## SageMath probe

The elliptic probe requires SageMath. With the documented conda environment:

```bash
conda run -n sage python experiments/formulations_comparison/sage_elliptic_probe.py
```

The integer-domain `D-probe` depends on the shared progression catalogue and is
not an autonomous search by elliptic height.

## Package integrity

- `MANIFEST.json` records source paths, release paths, sizes and SHA-256 hashes.
- `SHA256SUMS` provides a compact checksum list.
- `RELEASE_NOTES.md` states scope and known limitations.
- `docs/final_publication_audit.md` records the final pre-release checks.

## License

This package is distributed under the MIT License. See `LICENSE`.
