import traceback

from fastapi import APIRouter, HTTPException, Query, Depends

from services.dependencies import get_explorer_service
from services.explorer_service import ExplorerService

router = APIRouter()


@router.get("/map")
def get_embedding_map(
    hsk_level: str = Query("all"),
    method: str = Query("umap"),
    explorer_service: ExplorerService = Depends(get_explorer_service),
):
    try:
        return explorer_service.get_embedding_map(hsk_level, method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character}/neighbors")
def get_character_neighbors(
    character: str,
    limit: int = Query(5, ge=1, le=20),
    explorer_service: ExplorerService = Depends(get_explorer_service),
):
    try:
        return explorer_service.get_character_neighbors(character, limit)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))