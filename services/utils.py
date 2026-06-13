import json
import math
import os
from pathlib import Path

import pandas


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

CONFUSION_MAPS_DIR = ASSETS_DIR / "confusion_maps"
EMBEDDINGS_DIR = ASSETS_DIR / "embeddings"
EXCEL_PATH = ASSETS_DIR / "General_Standard_Hanzi.xlsx"


# -------------------------------------------------------------------
# In-memory asset cache
# -------------------------------------------------------------------

ASSETS_LOADED = False

CHAR_TO_PINYIN: dict[str, str] = {}

CONFUSION_MAPS: dict[str, dict] = {}

PROJECTION_MAPS: dict[str, list[dict]] = {}


# -------------------------------------------------------------------
# Startup loading
# -------------------------------------------------------------------

def load_assets_into_memory() -> None:
    global ASSETS_LOADED

    if ASSETS_LOADED:
        return

    print("Loading HanziTwins assets into memory...")

    _load_char_to_pinyin_into_memory()
    _load_confusion_maps_into_memory()
    _load_projection_maps_into_memory()

    ASSETS_LOADED = True

    print("Assets loaded successfully.")
    print(f"Loaded {len(CHAR_TO_PINYIN)} pinyin entries.")
    print(f"Loaded {len(CONFUSION_MAPS)} confusion maps.")
    print(f"Loaded {len(PROJECTION_MAPS)} projection maps.")


def _load_char_to_pinyin_into_memory() -> None:
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Excel metadata file not found: {EXCEL_PATH}")

    df = pandas.read_excel(EXCEL_PATH)

    if "Character" not in df.columns:
        raise ValueError("Excel file must contain a 'Character' column.")

    if "Pinyin" not in df.columns:
        raise ValueError("Excel file must contain a 'Pinyin' column.")

    df = df.dropna(subset=["Character", "Pinyin"])

    CHAR_TO_PINYIN.clear()

    for _, row in df.iterrows():
        character = str(row["Character"]).strip()
        pinyin = str(row["Pinyin"]).strip()

        if not character:
            continue

        if not pinyin or pinyin.lower() == "nan":
            continue

        CHAR_TO_PINYIN[character] = pinyin


def _load_confusion_maps_into_memory() -> None:
    if not CONFUSION_MAPS_DIR.exists():
        raise FileNotFoundError(f"Confusion maps directory not found: {CONFUSION_MAPS_DIR}")

    CONFUSION_MAPS.clear()

    for file_path in CONFUSION_MAPS_DIR.glob("confusion_map*.json"):
        key = _confusion_map_key_from_filename(file_path.name)

        with open(file_path, "r", encoding="utf-8") as file:
            CONFUSION_MAPS[key] = json.load(file)

    if "all" not in CONFUSION_MAPS:
        raise FileNotFoundError("Required confusion_map_full.json was not found.")


def _confusion_map_key_from_filename(filename: str) -> str:
    if filename == "confusion_map_full.json":
        return "all"

    prefix = "confusion_map_hsk_"
    suffix = ".json"

    if filename.startswith(prefix) and filename.endswith(suffix):
        return filename.removeprefix(prefix).removesuffix(suffix)

    # fallback, mostly for debugging
    return filename.removesuffix(".json")


def _load_projection_maps_into_memory() -> None:
    PROJECTION_MAPS.clear()

    projection_files = {
        "umap": EMBEDDINGS_DIR / "embedding_projection_umap.json",
        "tsne": EMBEDDINGS_DIR / "embedding_projection_tsne.json",
    }

    for method, file_path in projection_files.items():
        if not file_path.exists():
            print(f"Warning: projection file not found: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as file:
            PROJECTION_MAPS[method] = json.load(file)


def ensure_assets_loaded() -> None:
    if not ASSETS_LOADED:
        load_assets_into_memory()


# -------------------------------------------------------------------
# Runtime accessors
# -------------------------------------------------------------------

def get_confusion_map(hsk_level: str) -> dict:
    ensure_assets_loaded()

    key = normalize_hsk_level(hsk_level)

    if key is None or key == "all":
        key = "all"

    if key not in CONFUSION_MAPS:
        raise FileNotFoundError(f"Data for character set not found: {hsk_level}")

    return CONFUSION_MAPS[key]


def get_char_to_pinyin_map() -> dict[str, str]:
    ensure_assets_loaded()
    return CHAR_TO_PINYIN


def get_projection_map(method: str) -> list[dict]:
    ensure_assets_loaded()

    method = method.lower().strip()

    if method not in PROJECTION_MAPS:
        raise FileNotFoundError(f"Projection data not found for method: {method}")

    return PROJECTION_MAPS[method]


# -------------------------------------------------------------------
# Pinyin helpers
# -------------------------------------------------------------------

def get_safe_pinyin(character: str) -> str:
    value = get_char_to_pinyin_map().get(character)

    if value is None:
        return character

    if pandas.isna(value):
        return character

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return character

    return value


def get_valid_pinyin(character: str) -> str | None:
    value = get_char_to_pinyin_map().get(character)

    if value is None:
        return None

    if pandas.isna(value):
        return None

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return None

    return value


# -------------------------------------------------------------------
# Other helpers
# -------------------------------------------------------------------

def get_safe_similarity(score) -> float:
    try:
        score = float(score)
    except (TypeError, ValueError):
        return 0.0

    if not math.isfinite(score):
        return 0.0

    return round(score, 4)


def get_difficulty_start_index(difficulty: str) -> int:
    difficulty = difficulty.lower()

    if difficulty == "hard":
        return 0

    if difficulty == "medium":
        return 2

    return 4


def normalize_hsk_level(value):
    if value is None:
        return None

    value = str(value).lower().strip()

    if value == "nan" or value == "":
        return None

    return value


def load_json_file(path: str):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Required data file not found: {file_path.name}")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)