from fastapi import Query

from services.utils import (
    get_projection_map,
    normalize_hsk_level,
    get_valid_pinyin,
    get_safe_similarity,
    get_confusion_map,
)


class ExplorerService:
    def get_embedding_map(
        self,
        hsk_level: str = Query("all"),
        method: str = Query("umap"),
    ):
        method = method.lower()

        if method not in {"umap", "tsne"}:
            raise ValueError("Projection method must be either 'umap' or 'tsne'.")

        projection_data = get_projection_map(method)

        if hsk_level.lower() != "all":
            projection_data = [
                point for point in projection_data
                if normalize_hsk_level(point.get("hsk_level")) == normalize_hsk_level(hsk_level)
            ]

        return {
            "metadata": {
                "hsk_level": hsk_level,
                "method": method,
                "count": len(projection_data),
            },
            "points": projection_data,
        }

    def get_character_neighbors(
        self,
        character: str,
        limit: int = Query(5, ge=1, le=20),
    ):
        confusion_map = get_confusion_map("all")

        if character not in confusion_map:
            raise LookupError(f"Character {character} not found in confusion map.")

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