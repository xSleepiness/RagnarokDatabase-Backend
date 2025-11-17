# Ragnarok Online Database API

A FastAPI-based REST API for accessing Ragnarok Online game data (items and monsters) from rAthena database YAML files.

## Features

- 🎮 Comprehensive item database (usable, equipment, etc.)
- 👹 Complete monster database with stats and drops
- 📊 JSON API responses
- 🔍 Search and filter capabilities
- ⚡ **All data loaded in RAM for ultra-fast responses**
- 📝 Uses rAthena YAML database format
- 🖼️ **Automatic item image downloading and caching**
- 📈 **Popularity tracking system** (Today, Yesterday, Last 7 Days, Last 30 Days)
- 💾 **File-based persistence** for view statistics

## Data Source

This API uses the official **rAthena database format** (YAML files) located in `data/pre-re/`:
- `item_db_usable.yml` - Consumable items
- `item_db_equip.yml` - Equipment items
- `item_db_etc.yml` - Miscellaneous items
- `mob_db.yml` - Monster database
- `itemInfo.lua` - Item descriptions (identified descriptions only)

**Performance**: All data is loaded into RAM on startup using a singleton pattern for instant O(1) lookups by ID and fast filtering operations.

**Images**: Item images are automatically downloaded from Divine Pride API and cached locally in `data/images/` directory for faster access. The API checks for existing images on startup and only downloads missing ones with a 1-second delay between requests to avoid overloading the API.

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure as needed

## Running the API

```powershell
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

On startup, you'll see:
```
============================================================
🚀 Starting Ragnarok Online Database API
============================================================
Loading item descriptions from itemInfo.lua...
✓ Loaded XXXX item descriptions
Loading items into RAM...
✓ Loaded XXXX items
Loading monsters into RAM...
✓ Loaded XXXX monsters
============================================================
🖼️  Checking item images...
============================================================
📊 Item images: XXXX/XXXX already cached
📊 Collection images: XXXX/XXXX already cached
📥 Downloading XXX missing images...
⏱️  Estimated time: ~XXX seconds
============================================================
✅ Downloaded XX new images
============================================================
✅ API Ready - All data loaded in RAM for fast responses!
============================================================
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### Items
- `GET /api/v1/items` - Get all items (with pagination)
- `GET /api/v1/items/{item_id}` - Get item by ID (O(1) lookup, tracks popularity)
- `GET /api/v1/items/search/by-name?name={name}&exact={bool}` - Search items by name
- `GET /api/v1/items/filter/by-type?item_type={type}` - Filter items by type
- `GET /api/v1/items/popular/{period}?limit={n}` - Get popular items (period: today, yesterday, last7days, last30days)
- `GET /api/v1/items/{item_id}/stats` - Get view statistics for a specific item

### Monsters
- `GET /api/v1/monsters` - Get all monsters (with pagination)
- `GET /api/v1/monsters/{monster_id}` - Get monster by ID (O(1) lookup)
- `GET /api/v1/monsters/search/by-name?name={name}&exact={bool}` - Search monsters by name
- `GET /api/v1/monsters/filter/by-element?element={element}` - Filter monsters by element
- `GET /api/v1/monsters/filter/mvp` - Get all MVP monsters

### Utility
- `GET /` - API information
- `GET /health` - Health check with cache statistics

## Project Structure

```
RagnarokDatabaseFastAPI/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # Project documentation
├── api/
│   ├── routes/            # API route handlers
│   │   ├── items.py       # Item endpoints + popularity tracking
│   │   └── monsters.py    # Monster endpoints
│   └── models/            # Pydantic models
│       ├── item.py        # Item model (with image URLs)
│       └── monster.py     # Monster model
├── core/
│   ├── config.py          # Configuration management
│   ├── data_loader.py     # YAML data loading (RAM cache)
│   ├── image_manager.py   # Image downloading and caching
│   └── popularity_tracker.py  # View tracking with file persistence
└── data/
    ├── pre-re/            # rAthena pre-renewal database
    │   ├── item_db_usable.yml
    │   ├── item_db_equip.yml
    │   ├── item_db_etc.yml
    │   ├── mob_db.yml
    │   └── itemInfo.lua   # Item descriptions
    ├── images/            # Cached item images
    │   ├── item/          # Regular item images
    │   └── collection/    # Collection images
    └── popularity_data.json  # View statistics (persisted)
```

## Performance Notes

- **RAM Cache**: All data is loaded once on startup and kept in memory
- **Singleton Pattern**: Single DataLoader instance ensures data is loaded only once
- **O(1) Lookups**: ID-based queries use dictionary lookups for instant access
- **Fast Filtering**: In-memory filtering provides sub-millisecond response times
- **Image Caching**: Images are downloaded once and served locally via static files
- **Async Downloads**: Images are downloaded asynchronously with rate limiting (1 second delay)
- **Persistent Statistics**: View counts are saved to JSON file and survive server restarts

## Image Management

The API automatically manages item images from Divine Pride:

### Image Sources
- **Item images**: `https://static.divine-pride.net/images/items/item/{id}.png`
- **Collection images**: `https://static.divine-pride.net/images/items/collection/{id}.png`

### Image Caching
- Images are stored in `data/images/item/` and `data/images/collection/`
- On startup, the API checks for existing images and only downloads missing ones
- Downloaded images are served via `/static/images/item/{id}.png` and `/static/images/collection/{id}.png`
- Rate limiting: 1-second delay between downloads to avoid overloading the API
- Concurrent downloads: Maximum 5 simultaneous connections

### Image URLs in API Response
Each item includes:
- `image_url`: URL to the item icon image (local if cached, remote otherwise)
- `collection_image_url`: URL to the collection image (local if cached, remote otherwise)

## Popularity Tracking

The API tracks item views and provides statistics across different time periods:

### Features
- **Automatic Tracking**: Every time an item is accessed via `/api/v1/items/{item_id}`, a view is recorded
- **Time Periods**: Statistics available for Today, Yesterday, Last 7 Days, and Last 30 Days
- **File Persistence**: View data is stored in `data/popularity_data.json` and persists across server restarts
- **Thread-Safe**: Concurrent requests are handled safely with locking mechanisms

### Popularity Endpoints
- `GET /api/v1/items/popular/{period}?limit=10` - Get top items for a time period
  - Valid periods: `today`, `yesterday`, `last7days`, `last30days`
- `GET /api/v1/items/{item_id}/stats` - Get all statistics for a specific item
