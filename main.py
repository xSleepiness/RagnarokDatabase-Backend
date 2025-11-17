"""
Ragnarok Online Database API
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from api.routes import items, monsters
from core.data_loader import DataLoader
from core.image_manager import ImageManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data into RAM on startup and download missing images"""
    print("=" * 60)
    print("🚀 Starting Ragnarok Online Database API")
    print("=" * 60)
    
    # Initialize DataLoader - this loads all data into RAM
    data_loader = DataLoader()
    
    # Initialize ImageManager and download missing images
    image_manager = ImageManager()
    item_ids = [item.id for item in data_loader.get_items()]
    
    # Download missing images (both item and collection types)
    await image_manager.download_missing_images(
        item_ids=item_ids,
        download_both_types=True,
        max_concurrent=5
    )
    
    print("=" * 60)
    print("✅ API Ready - All data loaded in RAM for fast responses!")
    print("=" * 60)
    yield
    
    # Cleanup on shutdown
    print("Shutting down...")


app = FastAPI(
    title="Ragnarok Online Database API",
    description="API for retrieving Ragnarok Online items and monsters data",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving cached images
app.mount("/static/images", StaticFiles(directory="data/images"), name="images")

# Include routers
app.include_router(items.router, prefix="/api/v1", tags=["Items"])
app.include_router(monsters.router, prefix="/api/v1", tags=["Monsters"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Ragnarok Online Database API",
        "version": "1.0.0",
        "status": "All data loaded in RAM",
        "endpoints": {
            "items": "/api/v1/items",
            "monsters": "/api/v1/monsters",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    data_loader = DataLoader()
    item_count = len(data_loader.get_items())
    monster_count = len(data_loader.get_monsters())
    
    return {
        "status": "healthy",
        "items_loaded": item_count,
        "monsters_loaded": monster_count,
        "cache_status": "active"
    }
