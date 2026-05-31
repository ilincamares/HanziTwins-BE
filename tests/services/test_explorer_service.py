import math

import pytest

import services.explorer_service as explorer_module
from services.explorer_service import ExplorerService


FAKE_PROJECTION = [
    {
        "character": "你",
        "pinyin": "nǐ",
        "hsk_level": "1",
        "x": 0.1,
        "y": 0.2,
        "cluster": 0,
    },
    {
        "character": "好",
        "pinyin": "hǎo",
        "hsk_level": "1",
        "x": 0.3,
        "y": 0.4,
        "cluster": 0,
    },
    {
        "character": "学",
        "pinyin": "xué",
        "hsk_level": "2",
        "x": 0.5,
        "y": 0.6,
        "cluster": 1,
    },
]


FAKE_CONFUSION_MAP = {
    "你": [
        ["他", 95.123456],
        ["们", 91.0],
        ["好", float("nan")],
    ],
    "好": [
        ["妈", 94.0],
    ],
}


FAKE_PINYIN = {
    "你": "nǐ",
    "他": "tā",
    "们": "men",
    "好": "hǎo",
    "妈": "mā",
}


@pytest.fixture(autouse=True)
def patch_explorer_assets(monkeypatch):
    def fake_get_projection_map(method: str):
        if method not in {"umap", "tsne"}:
            raise FileNotFoundError(f"Projection data not found for method: {method}")

        return list(FAKE_PROJECTION)

    def fake_get_confusion_map(hsk_level: str):
        return FAKE_CONFUSION_MAP

    def fake_get_valid_pinyin(character: str):
        return FAKE_PINYIN.get(character)

    def fake_get_safe_similarity(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return 0.0

        if not math.isfinite(value):
            return 0.0

        return round(value, 4)

    monkeypatch.setattr(
        explorer_module,
        "get_projection_map",
        fake_get_projection_map,
        raising=False,
    )

    monkeypatch.setattr(
        explorer_module,
        "get_confusion_map",
        fake_get_confusion_map,
        raising=False,
    )

    monkeypatch.setattr(
        explorer_module,
        "get_valid_pinyin",
        fake_get_valid_pinyin,
        raising=False,
    )

    monkeypatch.setattr(
        explorer_module,
        "get_safe_similarity",
        fake_get_safe_similarity,
        raising=False,
    )


def test_get_embedding_map_returns_all_points():
    service = ExplorerService()

    result = service.get_embedding_map(
        hsk_level="all",
        method="umap",
    )

    assert result["metadata"]["hsk_level"] == "all"
    assert result["metadata"]["method"] == "umap"
    assert result["metadata"]["count"] == 3
    assert len(result["points"]) == 3


def test_get_embedding_map_filters_by_hsk_level():
    service = ExplorerService()

    result = service.get_embedding_map(
        hsk_level="1",
        method="umap",
    )

    assert result["metadata"]["hsk_level"] == "1"
    assert result["metadata"]["method"] == "umap"
    assert result["metadata"]["count"] == 2

    characters = [point["character"] for point in result["points"]]

    assert characters == ["你", "好"]


def test_get_embedding_map_accepts_tsne_method():
    service = ExplorerService()

    result = service.get_embedding_map(
        hsk_level="all",
        method="tsne",
    )

    assert result["metadata"]["method"] == "tsne"
    assert len(result["points"]) == 3


def test_get_embedding_map_normalizes_method_to_lowercase():
    service = ExplorerService()

    result = service.get_embedding_map(
        hsk_level="all",
        method="UMAP",
    )

    assert result["metadata"]["method"] == "umap"


def test_get_embedding_map_rejects_invalid_method():
    service = ExplorerService()

    with pytest.raises(ValueError, match="Projection method"):
        service.get_embedding_map(
            hsk_level="all",
            method="pca",
        )


def test_get_character_neighbors_returns_neighbors():
    service = ExplorerService()

    result = service.get_character_neighbors(
        character="你",
        limit=2,
    )

    assert result["character"] == "你"
    assert result["pinyin"] == "nǐ"

    assert len(result["neighbors"]) == 2

    assert result["neighbors"][0]["character"] == "他"
    assert result["neighbors"][0]["pinyin"] == "tā"
    assert result["neighbors"][0]["similarity"] == 95.1235

    assert result["neighbors"][1]["character"] == "们"
    assert result["neighbors"][1]["pinyin"] == "men"
    assert result["neighbors"][1]["similarity"] == 91.0


def test_get_character_neighbors_respects_limit():
    service = ExplorerService()

    result = service.get_character_neighbors(
        character="你",
        limit=1,
    )

    assert len(result["neighbors"]) == 1
    assert result["neighbors"][0]["character"] == "他"


def test_get_character_neighbors_converts_nan_similarity_to_zero():
    service = ExplorerService()

    result = service.get_character_neighbors(
        character="你",
        limit=3,
    )

    assert result["neighbors"][2]["character"] == "好"
    assert result["neighbors"][2]["similarity"] == 0.0


def test_get_character_neighbors_missing_character_raises_lookup_error():
    service = ExplorerService()

    with pytest.raises(LookupError, match="not found in confusion map"):
        service.get_character_neighbors(
            character="不存在",
            limit=5,
        )