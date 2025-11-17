"""Monster API routes"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from api.models.monster import Monster
from core.data_loader import DataLoader

router = APIRouter()
data_loader = DataLoader()


@router.get("/monsters", response_model=List[Monster])
async def get_all_monsters(
    skip: int = Query(0, ge=0, description="Number of monsters to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of monsters to return")
):
    """Get all monsters with pagination"""
    monsters = data_loader.get_monsters()
    return monsters[skip:skip + limit]


@router.get("/monsters/{monster_id}", response_model=Monster)
async def get_monster_by_id(monster_id: int):
    """Get a specific monster by ID"""
    monster = data_loader.get_monster_by_id(monster_id)
    if not monster:
        raise HTTPException(status_code=404, detail=f"Monster with ID {monster_id} not found")
    return monster


@router.get("/monsters/search/by-name", response_model=List[Monster])
async def search_monsters_by_name(
    name: str = Query(..., min_length=1, description="Monster name to search for"),
    exact: bool = Query(False, description="Exact match or partial match")
):
    """Search monsters by name"""
    monsters = data_loader.search_monsters_by_name(name, exact)
    if not monsters:
        raise HTTPException(status_code=404, detail=f"No monsters found matching '{name}'")
    return monsters


@router.get("/monsters/filter/by-element", response_model=List[Monster])
async def filter_monsters_by_element(
    element: str = Query(..., description="Element type to filter by")
):
    """Filter monsters by element"""
    monsters = data_loader.filter_monsters_by_element(element)
    if not monsters:
        raise HTTPException(status_code=404, detail=f"No monsters found with element '{element}'")
    return monsters


@router.get("/monsters/filter/mvp", response_model=List[Monster])
async def get_mvp_monsters():
    """Get all MVP monsters"""
    monsters = data_loader.get_mvp_monsters()
    if not monsters:
        raise HTTPException(status_code=404, detail="No MVP monsters found")
    return monsters
