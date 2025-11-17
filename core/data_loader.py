"""Data loading utilities for YAML files - Loads rAthena database format into RAM"""
import yaml
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from api.models.item import Item, ItemStats
from api.models.monster import Monster, MonsterStats, Drop
from core.config import settings
from core.image_manager import ImageManager


class DataLoader:
    """
    Handles loading and caching of rAthena YAML data files.
    All data is loaded into RAM on first access for maximum performance.
    """
    
    # Class-level cache (singleton pattern) - data persists in RAM
    _items_cache: Optional[Dict[int, Item]] = None
    _monsters_cache: Optional[Dict[int, Monster]] = None
    _item_descriptions_cache: Optional[Dict[int, str]] = None
    _image_manager: Optional[ImageManager] = None
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize and load all data into RAM on first instantiation"""
        if DataLoader._image_manager is None:
            DataLoader._image_manager = ImageManager()
        
        if DataLoader._item_descriptions_cache is None:
            print("Loading item descriptions from itemInfo.lua...")
            DataLoader._item_descriptions_cache = self._load_item_descriptions()
            print(f"✓ Loaded {len(DataLoader._item_descriptions_cache)} item descriptions")
        
        if DataLoader._items_cache is None:
            print("Loading items into RAM...")
            DataLoader._items_cache = self._load_all_items()
            print(f"✓ Loaded {len(DataLoader._items_cache)} items")
        
        if DataLoader._monsters_cache is None:
            print("Loading monsters into RAM...")
            DataLoader._monsters_cache = self._load_all_monsters()
            print(f"✓ Loaded {len(DataLoader._monsters_cache)} monsters")
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a rAthena YAML file"""
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}
    
    def _load_item_descriptions(self) -> Dict[int, str]:
        """
        Parse itemInfo.lua and extract identifiedDescriptionName for each item.
        Returns a dictionary mapping item IDs to their descriptions.
        """
        descriptions = {}
        
        if not settings.ITEMINFO_FILE.exists():
            print(f"Warning: itemInfo.lua not found at {settings.ITEMINFO_FILE}")
            return descriptions
        
        try:
            with open(settings.ITEMINFO_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse Lua table: look for [item_id] = { ... }
            # Split by item entries
            item_pattern = r'\[(\d+)\]\s*=\s*\{'
            
            # Find all item IDs and their positions
            matches = list(re.finditer(item_pattern, content))
            
            for i, match in enumerate(matches):
                item_id = int(match.group(1))
                start_pos = match.end()
                
                # Find the end of this item block (next item or end of table)
                if i < len(matches) - 1:
                    end_pos = matches[i + 1].start()
                else:
                    # Find the closing of the main table
                    end_pos = content.find('}', start_pos)
                    if end_pos == -1:
                        end_pos = len(content)
                
                item_block = content[start_pos:end_pos]
                
                # Extract identifiedDescriptionName array (NOT unidentifiedDescriptionName)
                # We need to explicitly look for "identified" not "unidentified"
                # Use a negative lookbehind to ensure we don't match "unidentifiedDescriptionName"
                desc_pattern = r'(?<!un)identifiedDescriptionName\s*=\s*\{(.*?)\}'
                desc_match = re.search(desc_pattern, item_block, re.DOTALL)
                
                if desc_match:
                    desc_content = desc_match.group(1)
                    
                    # Extract all quoted strings
                    lines = re.findall(r'"([^"]*)"', desc_content)
                    
                    # Clean up the lines
                    clean_lines = []
                    for line in lines:
                        # Remove color codes like ^FFFFFF, ^000000, ^0000FF, etc.
                        line = re.sub(r'\^[0-9A-Fa-f]{6}', '', line)
                        # Remove underscore separator lines
                        line = line.replace('_', '').strip()
                        if line and line != '...':
                            clean_lines.append(line)
                    
                    if clean_lines:
                        # Join lines with newline
                        descriptions[item_id] = '\n'.join(clean_lines)
            
        except Exception as e:
            print(f"Error parsing itemInfo.lua: {e}")
            import traceback
            traceback.print_exc()
        
        return descriptions
    
    def _parse_item(self, item_data: Dict[str, Any]) -> Item:
        """Parse rAthena item format to our Item model"""
        # Parse basic item data
        item_id = item_data.get('Id')
        name = item_data.get('Name', '')
        aegis_name = item_data.get('AegisName', '')
        item_type = item_data.get('Type', 'Etc')
        subtype = item_data.get('SubType')
        buy_price = item_data.get('Buy', 0)
        sell_price = item_data.get('Sell', buy_price // 2 if buy_price else 0)
        weight = item_data.get('Weight', 0)
        
        # Get description from itemInfo.lua cache
        description = DataLoader._item_descriptions_cache.get(item_id)
        if not description:
            description = f"{aegis_name} - {item_type}"
        
        # Parse stats
        stats = ItemStats(
            atk=item_data.get('Attack'),
            matk=item_data.get('MagicAttack'),
            defense=item_data.get('Defense'),
            weight=weight,
            slots=item_data.get('Slots', 0)
        )
        
        # Parse job requirements
        jobs_data = item_data.get('Jobs', {})
        required_job = None
        if jobs_data and jobs_data != {'All': True}:
            required_job = [job for job, allowed in jobs_data.items() if allowed]
        
        # Parse gender and location
        gender = item_data.get('Gender')
        locations = item_data.get('Locations')
        location = None
        if locations:
            if isinstance(locations, dict):
                location = ', '.join([loc for loc, enabled in locations.items() if enabled])
            elif isinstance(locations, str):
                location = locations
        
        return Item(
            id=item_id,
            name=name,
            description=description,
            type=item_type,
            subtype=str(subtype) if subtype else None,
            buy_price=buy_price,
            sell_price=sell_price,
            stats=stats,
            required_level=item_data.get('EquipLevelMin', 0),
            required_job=required_job,
            gender=gender,
            location=location,
            sprite=aegis_name.lower(),
            script=item_data.get('Script'),
            equip_script=item_data.get('EquipScript'),
            unequip_script=item_data.get('UnEquipScript'),
            image_url=DataLoader._image_manager.get_image_url(item_id, "item"),
            collection_image_url=DataLoader._image_manager.get_image_url(item_id, "collection")
        )
    
    def _parse_monster(self, mob_data: Dict[str, Any]) -> Monster:
        """Parse rAthena monster format to our Monster model"""
        monster_id = mob_data.get('Id')
        name = mob_data.get('Name', '')
        aegis_name = mob_data.get('AegisName', '')
        
        # Parse stats
        stats = MonsterStats(
            hp=mob_data.get('Hp', 1),
            sp=mob_data.get('Sp'),
            base_exp=mob_data.get('BaseExp', 0),
            job_exp=mob_data.get('JobExp', 0),
            atk=mob_data.get('Attack', 0),
            atk2=mob_data.get('Attack2'),
            defense=mob_data.get('Defense', 0),
            mdef=mob_data.get('MagicDefense', 0),
            **{'str': mob_data.get('Str', 1)},  # Use dict unpacking for 'str'
            agi=mob_data.get('Agi', 1),
            vit=mob_data.get('Vit', 1),
            **{'int': mob_data.get('Int', 1)},  # Use dict unpacking for 'int'
            dex=mob_data.get('Dex', 1),
            luk=mob_data.get('Luk', 1)
        )
        
        # Parse drops
        drops = []
        drops_data = mob_data.get('Drops', [])
        for drop in drops_data:
            if isinstance(drop, dict) and 'Item' in drop:
                drops.append(Drop(
                    item_id=0,  # We don't have item ID in drop data
                    item_name=drop['Item'],
                    rate=drop.get('Rate', 1) / 100  # Convert to percentage
                ))
        
        # Parse MVP drops
        mvp_drops = []
        mvp_drops_data = mob_data.get('MvpDrops', [])
        is_mvp = len(mvp_drops_data) > 0 or mob_data.get('MvpExp', 0) > 0
        
        for drop in mvp_drops_data:
            if isinstance(drop, dict) and 'Item' in drop:
                mvp_drops.append(Drop(
                    item_id=0,
                    item_name=drop['Item'],
                    rate=drop.get('Rate', 1) / 100
                ))
        
        return Monster(
            id=monster_id,
            name=name,
            level=mob_data.get('Level', 1),
            element=mob_data.get('Element', 'Neutral'),
            element_level=mob_data.get('ElementLevel', 1),
            race=mob_data.get('Race', 'Formless'),
            size=mob_data.get('Size', 'Small'),
            stats=stats,
            drops=drops if drops else None,
            mvp=is_mvp,
            mvp_drops=mvp_drops if mvp_drops else None,
            spawn_locations=None,  # rAthena doesn't store spawn locations in mob_db
            sprite=aegis_name.lower()
        )
    
    def _load_all_items(self) -> Dict[int, Item]:
        """Load all items from all item files into RAM"""
        items_dict = {}
        
        # Load from all item files
        item_files = [
            settings.ITEMS_USABLE_FILE,
            settings.ITEMS_EQUIP_FILE,
            settings.ITEMS_ETC_FILE
        ]
        
        for file_path in item_files:
            if not file_path.exists():
                continue
                
            data = self._load_yaml_file(file_path)
            body = data.get('Body', [])
            
            for item_data in body:
                try:
                    item = self._parse_item(item_data)
                    items_dict[item.id] = item
                except Exception as e:
                    print(f"Error parsing item {item_data.get('Id', 'unknown')}: {e}")
        
        return items_dict
    
    def _load_all_monsters(self) -> Dict[int, Monster]:
        """Load all monsters into RAM"""
        monsters_dict = {}
        
        data = self._load_yaml_file(settings.MONSTERS_FILE)
        body = data.get('Body', [])
        
        for mob_data in body:
            try:
                monster = self._parse_monster(mob_data)
                monsters_dict[monster.id] = monster
            except Exception as e:
                print(f"Error parsing monster {mob_data.get('Id', 'unknown')}: {e}")
        
        return monsters_dict
    
    # ===== Item Methods =====
    
    def get_items(self) -> List[Item]:
        """Get all items from RAM cache"""
        return list(DataLoader._items_cache.values())
    
    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        """Get a specific item by ID - O(1) lookup from RAM"""
        return DataLoader._items_cache.get(item_id)
    
    def search_items_by_name(self, name: str, exact: bool = False) -> List[Item]:
        """Search items by name"""
        name_lower = name.lower()
        items = DataLoader._items_cache.values()
        
        if exact:
            return [item for item in items if item.name.lower() == name_lower]
        return [item for item in items if name_lower in item.name.lower()]
    
    def filter_items_by_type(self, item_type: str) -> List[Item]:
        """Filter items by type"""
        type_lower = item_type.lower()
        return [item for item in DataLoader._items_cache.values() 
                if item.type.lower() == type_lower]
    
    # ===== Monster Methods =====
    
    def get_monsters(self) -> List[Monster]:
        """Get all monsters from RAM cache"""
        return list(DataLoader._monsters_cache.values())
    
    def get_monster_by_id(self, monster_id: int) -> Optional[Monster]:
        """Get a specific monster by ID - O(1) lookup from RAM"""
        return DataLoader._monsters_cache.get(monster_id)
    
    def search_monsters_by_name(self, name: str, exact: bool = False) -> List[Monster]:
        """Search monsters by name"""
        name_lower = name.lower()
        monsters = DataLoader._monsters_cache.values()
        
        if exact:
            return [monster for monster in monsters if monster.name.lower() == name_lower]
        return [monster for monster in monsters if name_lower in monster.name.lower()]
    
    def filter_monsters_by_element(self, element: str) -> List[Monster]:
        """Filter monsters by element"""
        element_lower = element.lower()
        return [monster for monster in DataLoader._monsters_cache.values() 
                if monster.element.lower() == element_lower]
    
    def get_mvp_monsters(self) -> List[Monster]:
        """Get all MVP monsters"""
        return [monster for monster in DataLoader._monsters_cache.values() if monster.mvp]
    
    def reload_data(self):
        """Force reload all data from YAML files (useful for updates)"""
        print("Reloading all data...")
        DataLoader._item_descriptions_cache = self._load_item_descriptions()
        DataLoader._items_cache = self._load_all_items()
        DataLoader._monsters_cache = self._load_all_monsters()
        print(f"✓ Reloaded {len(DataLoader._items_cache)} items and {len(DataLoader._monsters_cache)} monsters")
