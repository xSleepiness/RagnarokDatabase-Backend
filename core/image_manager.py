"""Image manager for downloading and caching item images"""
import asyncio
import aiohttp
from pathlib import Path
from typing import Set, List
from core.config import settings


class ImageManager:
    """
    Manages item images by downloading them from Divine Pride API
    and storing them locally for caching.
    """
    
    # Base URLs for image downloads
    ITEM_IMAGE_URL = "https://static.divine-pride.net/images/items/item/{item_id}.png"
    COLLECTION_IMAGE_URL = "https://static.divine-pride.net/images/items/collection/{item_id}.png"
    
    # Local directories
    IMAGES_DIR = Path("data/images")
    ITEM_DIR = IMAGES_DIR / "item"
    COLLECTION_DIR = IMAGES_DIR / "collection"
    
    # Delay between downloads to avoid overloading the API
    DOWNLOAD_DELAY = 1.0  # seconds
    
    def __init__(self):
        """Initialize image manager and ensure directories exist"""
        self.ITEM_DIR.mkdir(parents=True, exist_ok=True)
        self.COLLECTION_DIR.mkdir(parents=True, exist_ok=True)
        self._downloaded_count = 0
        self._failed_downloads: Set[int] = set()
    
    def _get_image_path(self, item_id: int, image_type: str = "item") -> Path:
        """Get the local path for an item image"""
        if image_type == "collection":
            return self.COLLECTION_DIR / f"{item_id}.png"
        return self.ITEM_DIR / f"{item_id}.png"
    
    def image_exists(self, item_id: int, image_type: str = "item") -> bool:
        """Check if an image already exists locally"""
        return self._get_image_path(item_id, image_type).exists()
    
    async def download_image(
        self, 
        session: aiohttp.ClientSession, 
        item_id: int, 
        image_type: str = "item"
    ) -> bool:
        """
        Download a single image from Divine Pride API
        
        Args:
            session: aiohttp ClientSession for making requests
            item_id: ID of the item
            image_type: "item" or "collection"
        
        Returns:
            True if downloaded successfully, False otherwise
        """
        # Skip if already exists
        if self.image_exists(item_id, image_type):
            return True
        
        # Get URL based on type
        if image_type == "collection":
            url = self.COLLECTION_IMAGE_URL.format(item_id=item_id)
        else:
            url = self.ITEM_IMAGE_URL.format(item_id=item_id)
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    image_data = await response.read()
                    
                    # Save image to disk
                    image_path = self._get_image_path(item_id, image_type)
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    self._downloaded_count += 1
                    return True
                else:
                    self._failed_downloads.add(item_id)
                    return False
        
        except asyncio.TimeoutError:
            print(f"⚠️  Timeout downloading {image_type} image for item {item_id}")
            self._failed_downloads.add(item_id)
            return False
        
        except Exception as e:
            print(f"⚠️  Error downloading {image_type} image for item {item_id}: {e}")
            self._failed_downloads.add(item_id)
            return False
    
    async def download_missing_images(
        self, 
        item_ids: List[int], 
        download_both_types: bool = True,
        max_concurrent: int = 5
    ):
        """
        Download missing images for a list of item IDs
        
        Args:
            item_ids: List of item IDs to check and download
            download_both_types: If True, downloads both item and collection images
            max_concurrent: Maximum number of concurrent downloads
        """
        print(f"\n{'='*60}")
        print("🖼️  Checking item images...")
        print(f"{'='*60}")
        
        # Count existing images
        existing_item = sum(1 for item_id in item_ids if self.image_exists(item_id, "item"))
        existing_collection = sum(1 for item_id in item_ids if self.image_exists(item_id, "collection"))
        
        print(f"📊 Item images: {existing_item}/{len(item_ids)} already cached")
        if download_both_types:
            print(f"📊 Collection images: {existing_collection}/{len(item_ids)} already cached")
        
        # Prepare download tasks
        tasks_to_download = []
        
        for item_id in item_ids:
            if not self.image_exists(item_id, "item"):
                tasks_to_download.append(("item", item_id))
            
            if download_both_types and not self.image_exists(item_id, "collection"):
                tasks_to_download.append(("collection", item_id))
        
        if not tasks_to_download:
            print("✅ All images already cached!")
            print(f"{'='*60}\n")
            return
        
        print(f"📥 Downloading {len(tasks_to_download)} missing images...")
        print(f"⏱️  Estimated time: ~{len(tasks_to_download) * 0.1:.1f} seconds")
        print(f"{'='*60}")
        
        # Create aiohttp session with connection pooling
        connector = aiohttp.TCPConnector(limit=max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Process downloads with rate limiting
            for i, (image_type, item_id) in enumerate(tasks_to_download, 1):
                await self.download_image(session, item_id, image_type)
                
                # Progress update every 50 downloads
                if i % 50 == 0:
                    print(f"  📥 Progress: {i}/{len(tasks_to_download)} images downloaded...")
                
                # Add delay to avoid overloading the API
                if i < len(tasks_to_download):  # Don't delay after the last download
                    await asyncio.sleep(0.1)  # 100ms delay - minimal but safe
        
        print(f"{'='*60}")
        print(f"✅ Downloaded {self._downloaded_count} new images")
        
        if self._failed_downloads:
            print(f"⚠️  Failed to download {len(self._failed_downloads)} images")
            print(f"   Failed item IDs: {sorted(list(self._failed_downloads))[:10]}...")
        
        print(f"{'='*60}\n")
    
    def get_image_url(self, item_id: int, image_type: str = "item") -> str:
        """
        Get the URL for an item image (local if exists, remote otherwise)
        
        Args:
            item_id: ID of the item
            image_type: "item" or "collection"
        
        Returns:
            URL string for the image
        """
        # Check if local image exists
        if self.image_exists(item_id, image_type):
            if image_type == "collection":
                return f"/static/images/collection/{item_id}.png"
            return f"/static/images/item/{item_id}.png"
        
        # Return remote URL if not cached
        if image_type == "collection":
            return self.COLLECTION_IMAGE_URL.format(item_id=item_id)
        return self.ITEM_IMAGE_URL.format(item_id=item_id)
    
    def clear_cache(self, image_type: str = None):
        """
        Clear cached images
        
        Args:
            image_type: "item", "collection", or None for all
        """
        if image_type == "item" or image_type is None:
            for image_file in self.ITEM_DIR.glob("*.png"):
                image_file.unlink()
        
        if image_type == "collection" or image_type is None:
            for image_file in self.COLLECTION_DIR.glob("*.png"):
                image_file.unlink()
        
        print(f"🗑️  Cleared {image_type or 'all'} image cache")
