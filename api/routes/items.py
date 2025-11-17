"""Item API routes"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import FileResponse
from api.models.item import Item
from core.data_loader import DataLoader
from core.popularity_tracker import PopularityTracker
from core.config import settings

router = APIRouter()
data_loader = DataLoader()
popularity_tracker = PopularityTracker()


@router.get("/items", response_model=List[Item])
async def get_all_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return")
):
    """Get all items with pagination"""
    items = data_loader.get_items()
    return items[skip:skip + limit]


@router.get("/items/search", response_model=List[Item])
async def search_items(
    query: str = Query(..., min_length=1, description="Search query - item name or ID"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results to return")
):
    """
    Universal search endpoint - searches by item name (partial match) or by ID if query is a number.
    Perfect for search bars in mobile apps.
    """
    # Check if query is a number (item ID search)
    if query.isdigit():
        item_id = int(query)
        item = data_loader.get_item_by_id(item_id)
        if item:
            return [item]
        # If not found by ID, continue to name search
    
    # Search by name (partial match, case-insensitive)
    items = data_loader.search_items_by_name(query, exact=False)
    
    if not items:
        raise HTTPException(status_code=404, detail=f"No items found matching '{query}'")
    
    return items[:limit]


@router.get("/items/search/by-name", response_model=List[Item])
async def search_items_by_name(
    name: str = Query(..., min_length=1, description="Item name to search for"),
    exact: bool = Query(False, description="Exact match or partial match"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results to return")
):
    """Search items by name (partial or exact match)"""
    items = data_loader.search_items_by_name(name, exact)
    if not items:
        raise HTTPException(status_code=404, detail=f"No items found matching '{name}'")
    return items[:limit]


@router.get("/items/filter/by-type", response_model=List[Item])
async def filter_items_by_type(
    item_type: str = Query(..., description="Item type to filter by")
):
    """Filter items by type"""
    items = data_loader.filter_items_by_type(item_type)
    if not items:
        raise HTTPException(status_code=404, detail=f"No items found of type '{item_type}'")
    return items


@router.get("/items/popular/{period}")
async def get_popular_items(
    period: str = Path(..., description="Time period: today, yesterday, last7days, last30days"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return")
):
    """Get most popular items for a specific time period"""
    valid_periods = ["today", "yesterday", "last7days", "last30days"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    
    popular_items = popularity_tracker.get_popular_items(period=period, limit=limit)
    
    # Enrich with item details
    result = []
    for item_stat in popular_items:
        item = data_loader.get_item_by_id(item_stat["item_id"])
        if item:
            result.append({
                "item_id": item.id,
                "name": item.name,
                "type": item.type,
                "view_count": item_stat["view_count"],
                "sprite": item.sprite
            })
    
    return {
        "period": period,
        "items": result
    }


@router.get("/items/images/item/{item_id}")
@router.get("/items/images/item/{item_id}.png")
async def get_item_image(
    item_id: int = Path(..., ge=1, description="Item ID (positive integer only)")
):
    """Get item image by ID. Returns [not_found].png if image doesn't exist."""
    image_path = settings.IMAGES_DIR / "item" / f"{item_id}.png"
    not_found_path = settings.IMAGES_DIR / "item" / "[not_found].png"
    
    # Check if specific image exists
    if image_path.exists():
        return FileResponse(
            path=str(image_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
        )
    
    # Return not found image if it exists
    if not_found_path.exists():
        return FileResponse(
            path=str(not_found_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
    
    # If even not_found image doesn't exist, return 404
    raise HTTPException(status_code=404, detail="Image not found and fallback image is missing")


@router.get("/items/images/collection/{item_id}")
@router.get("/items/images/collection/{item_id}.png")
async def get_collection_image(
    item_id: int = Path(..., ge=1, description="Item ID (positive integer only)")
):
    """Get collection image by ID. Returns [not_found].png if image doesn't exist."""
    image_path = settings.IMAGES_DIR / "collection" / f"{item_id}.png"
    not_found_path = settings.IMAGES_DIR / "collection" / "[not_found].png"
    
    # Check if specific image exists
    if image_path.exists():
        return FileResponse(
            path=str(image_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
        )
    
    # Return not found image if it exists
    if not_found_path.exists():
        return FileResponse(
            path=str(not_found_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
    
    # If even not_found image doesn't exist, return 404
    raise HTTPException(status_code=404, detail="Image not found and fallback image is missing")


@router.get("/items/{item_id}/stats")
async def get_item_stats(item_id: int):
    """Get view statistics for a specific item across all time periods"""
    item = data_loader.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    stats = popularity_tracker.get_item_stats(item_id)
    
    return {
        "item_id": item.id,
        "name": item.name,
        "statistics": stats
    }


@router.get("/items/{item_id}", response_model=Item)
async def get_item_by_id(item_id: int):
    """Get a specific item by ID"""
    item = data_loader.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    # Track this view for popularity statistics
    popularity_tracker.track_view(item_id)
    
    return item


@router.get("/items/images/item/{item_id}")
@router.get("/items/images/item/{item_id}.png")
async def get_item_image(
    item_id: int = Path(..., ge=1, description="Item ID (positive integer only)")
):
    """Get item image by ID. Returns [not_found].png if image doesn't exist."""
    image_path = settings.IMAGES_DIR / "item" / f"{item_id}.png"
    not_found_path = settings.IMAGES_DIR / "item" / "[not_found].png"
    
    # Check if specific image exists
    if image_path.exists():
        return FileResponse(
            path=str(image_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
        )
    
    # Return not found image if it exists
    if not_found_path.exists():
        return FileResponse(
            path=str(not_found_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
    
    # If even not_found image doesn't exist, return 404
    raise HTTPException(status_code=404, detail="Image not found and fallback image is missing")


@router.get("/items/images/collection/{item_id}")
@router.get("/items/images/collection/{item_id}.png")
async def get_collection_image(
    item_id: int = Path(..., ge=1, description="Item ID (positive integer only)")
):
    """Get collection image by ID. Returns [not_found].png if image doesn't exist."""
    image_path = settings.IMAGES_DIR / "collection" / f"{item_id}.png"
    not_found_path = settings.IMAGES_DIR / "collection" / "[not_found].png"
    
    # Check if specific image exists
    if image_path.exists():
        return FileResponse(
            path=str(image_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
        )
    
    # Return not found image if it exists
    if not_found_path.exists():
        return FileResponse(
            path=str(not_found_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
    
    # If even not_found image doesn't exist, return 404
    raise HTTPException(status_code=404, detail="Image not found and fallback image is missing")
