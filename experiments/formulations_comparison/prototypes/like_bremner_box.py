"""Borne de boîte complète pour le prototype like-Bremner."""

from __future__ import annotations

from .like_bremner import LikeBremnerSearchResult, search_like_bremner
from .model import ArithmeticProgression


def search_like_bremner_box(
    complete_box_root: int,
    *,
    primitive_only: bool = True,
    progressions: tuple[ArithmeticProgression, ...] | None = None,
    early_primitive_filter: bool = True,
) -> LikeBremnerSearchResult:
    """Impose ``0 < case <= complete_box_root²`` sur les neuf valeurs de la grille.

    La fonction de base borne les racines des sept cases carrées. Cette couche
    ajoute la borne de magnitude nécessaire aux deux cases non carrées ; c'est
    cette convention qui place la première apparition de Bremner à ``R=601``.
    """

    result = search_like_bremner(
        complete_box_root,
        primitive_only=primitive_only,
        progressions=progressions,
        early_primitive_filter=early_primitive_filter,
    )
    upper = complete_box_root * complete_box_root
    kept = tuple(hit for hit in result.hits if max(hit.grid) <= upper)
    stats = dict(result.stats)
    stats["pre_box_classes"] = len(result.hits)
    stats["rejected_outside_complete_box"] = len(result.hits) - len(kept)
    stats["accepted_classes"] = len(kept)
    return LikeBremnerSearchResult(result.formulation + "-box", complete_box_root, kept, stats)
