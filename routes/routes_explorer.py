import json
import math
import os

import pandas
from fastapi import APIRouter, HTTPException, Query

from routes.routes_quiz import CHAR_TO_PINYIN

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECTION_FILES = {
    "umap": os.path.join(BASE_DIR, "assets", "embeddings", "embedding_projection_umap.json"),
    "tsne": os.path.join(BASE_DIR, "assets", "embeddings", "embedding_projection_tsne.json"),
}

CONFUSION_MAP_PATH = os.path.join(
    BASE_DIR,
    "assets",
    "confusion_maps",
    "confusion_map_full.json"
)


def load_json_file(path: str):
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail=f"Required data file not found: {os.path.basename(path)}"
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_hsk_level(value):
    if value is None:
        return None

    value = str(value).lower().strip()

    if value == "nan" or value == "":
        return None

    return value


def get_valid_pinyin(character: str) -> str | None:
    value = CHAR_TO_PINYIN.get(character)

    if value is None:
        return None

    if pandas.isna(value):
        return None

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return None

    return value


def get_safe_similarity(score) -> float:
    try:
        score = float(score)
    except (TypeError, ValueError):
        return 0.0

    if not math.isfinite(score):
        return 0.0

    return score

@router.get("/map")
def get_embedding_map(
    hsk_level: str = Query("all"),
    method: str = Query("umap"),
):
    method = method.lower()

    if method not in PROJECTION_FILES:
        raise HTTPException(
            status_code=400,
            detail="Projection method must be either 'umap' or 'tsne'."
        )

    projection_data = load_json_file(PROJECTION_FILES[method])

    if hsk_level.lower() != "all":
        projection_data = [
            point for point in projection_data
            if normalize_hsk_level(point.get("hsk_level")) == hsk_level
        ]

    return {
        "metadata": {
            "hsk_level": hsk_level,
            "method": method,
            "count": len(projection_data),
        },
        "points": projection_data,
    }

@router.get("/{character}/neighbors")
def get_character_neighbors(
    character: str,
    limit: int = Query(5, ge=1, le=20),
):
    confusion_map = load_json_file(CONFUSION_MAP_PATH)

    if character not in confusion_map:
        raise HTTPException(
            status_code=404,
            detail=f"Character {character} not found in confusion map."
        )

    neighbors = []

    for neighbor_character, similarity in confusion_map[character][:limit]:
        pinyin = get_valid_pinyin(neighbor_character)

        neighbors.append(
            {
                "character": neighbor_character,
                "pinyin": pinyin,
                "similarity": get_safe_similarity(similarity),
            }
        )

    return {
        "character": character,
        "pinyin": get_valid_pinyin(character),
        "neighbors": neighbors,
    }