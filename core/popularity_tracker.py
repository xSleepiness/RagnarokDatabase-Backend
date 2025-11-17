"""Item popularity tracking system"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from threading import Lock
from pathlib import Path
import json


class PopularityTracker:
    """
    Tracks item view counts with time-based statistics.
    Singleton pattern to maintain state across requests.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(PopularityTracker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize tracking data structures"""
        if self._initialized:
            return
            
        # File path for persistence
        self._data_file = Path(__file__).parent.parent / "data" / "popularity_data.json"
        
        # Store view events with timestamps: {item_id: [timestamp1, timestamp2, ...]}
        self._view_history: Dict[int, List[datetime]] = defaultdict(list)
        
        # Load existing data from file
        self._load_from_file()
        
        self._initialized = True
    
    def track_view(self, item_id: int):
        """Record a view for an item"""
        with self._lock:
            self._view_history[item_id].append(datetime.now())
            # Save to file after each view (could be optimized with batching)
            self._save_to_file()
    
    def _get_views_in_period(self, item_id: int, start_time: datetime) -> int:
        """Count views for an item since start_time"""
        views = self._view_history.get(item_id, [])
        return sum(1 for timestamp in views if timestamp >= start_time)
    
    def get_popular_items(self, period: str = "today", limit: int = 10) -> List[Dict[str, int]]:
        """
        Get most popular items for a time period.
        
        Args:
            period: 'today', 'yesterday', 'last7days', 'last30days'
            limit: Maximum number of items to return
            
        Returns:
            List of dicts with item_id and view_count, sorted by popularity
        """
        now = datetime.now()
        
        # Define time periods
        if period == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "yesterday":
            yesterday = now - timedelta(days=1)
            start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "last7days":
            start_time = now - timedelta(days=7)
        elif period == "last30days":
            start_time = now - timedelta(days=30)
        else:
            raise ValueError(f"Invalid period: {period}")
        
        # Count views for each item in the period
        item_counts = []
        
        with self._lock:
            for item_id, timestamps in self._view_history.items():
                if period == "yesterday":
                    # Special case: only count views from yesterday
                    count = sum(1 for ts in timestamps if start_time <= ts < end_time)
                else:
                    count = sum(1 for ts in timestamps if ts >= start_time)
                
                if count > 0:
                    item_counts.append({"item_id": item_id, "view_count": count})
        
        # Sort by view count (descending) and return top items
        item_counts.sort(key=lambda x: x["view_count"], reverse=True)
        return item_counts[:limit]
    
    def get_item_stats(self, item_id: int) -> Dict[str, int]:
        """Get view statistics for a specific item across all periods"""
        now = datetime.now()
        
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        last7days_start = now - timedelta(days=7)
        last30days_start = now - timedelta(days=30)
        
        views = self._view_history.get(item_id, [])
        
        return {
            "item_id": item_id,
            "today": sum(1 for ts in views if ts >= today_start),
            "yesterday": sum(1 for ts in views if yesterday_start <= ts < today_start),
            "last7days": sum(1 for ts in views if ts >= last7days_start),
            "last30days": sum(1 for ts in views if ts >= last30days_start),
            "all_time": len(views)
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Remove view data older than specified days to prevent memory bloat"""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        with self._lock:
            for item_id in list(self._view_history.keys()):
                # Filter out old timestamps
                self._view_history[item_id] = [
                    ts for ts in self._view_history[item_id] 
                    if ts >= cutoff_time
                ]
                
                # Remove item if no recent views
                if not self._view_history[item_id]:
                    del self._view_history[item_id]
            
            # Save cleaned data to file
            self._save_to_file()
    
    def _save_to_file(self):
        """Save view history to JSON file"""
        try:
            # Ensure directory exists
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert datetime objects to ISO format strings
            data_to_save = {}
            for item_id, timestamps in self._view_history.items():
                data_to_save[str(item_id)] = [ts.isoformat() for ts in timestamps]
            
            # Write to file
            with open(self._data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            print(f"Error saving popularity data: {e}")
    
    def _load_from_file(self):
        """Load view history from JSON file"""
        if not self._data_file.exists():
            print("No existing popularity data found, starting fresh")
            return
        
        try:
            with open(self._data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert ISO format strings back to datetime objects
            for item_id_str, timestamp_strings in data.items():
                item_id = int(item_id_str)
                self._view_history[item_id] = [
                    datetime.fromisoformat(ts) for ts in timestamp_strings
                ]
            
            print(f"✓ Loaded popularity data for {len(self._view_history)} items from file")
        except Exception as e:
            print(f"Error loading popularity data: {e}")
            print("Starting with empty popularity data")
