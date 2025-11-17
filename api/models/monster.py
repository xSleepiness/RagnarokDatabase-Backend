"""Monster data models"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class MonsterStats(BaseModel):
    """Monster statistics"""
    hp: int = Field(..., description="Hit points")
    sp: Optional[int] = Field(None, description="Skill points")
    base_exp: int = Field(..., description="Base experience")
    job_exp: int = Field(..., description="Job experience")
    atk: int = Field(..., description="Attack power")
    atk2: Optional[int] = Field(None, description="Secondary attack")
    defense: int = Field(..., description="Defense")
    mdef: int = Field(..., description="Magic defense")
    str: int = Field(..., description="Strength", alias="str")
    agi: int = Field(..., description="Agility")
    vit: int = Field(..., description="Vitality")
    int_stat: int = Field(..., description="Intelligence", alias="int")
    dex: int = Field(..., description="Dexterity")
    luk: int = Field(..., description="Luck")
    
    model_config = {"populate_by_name": True}


class Drop(BaseModel):
    """Item drop information"""
    item_id: int = Field(..., description="Item ID")
    item_name: str = Field(..., description="Item name")
    rate: float = Field(..., description="Drop rate percentage")


class Monster(BaseModel):
    """Ragnarok Online Monster model"""
    id: int = Field(..., description="Unique monster ID")
    name: str = Field(..., description="Monster name")
    level: int = Field(..., description="Monster level")
    element: str = Field(..., description="Element type")
    element_level: int = Field(..., description="Element level (1-4)")
    race: str = Field(..., description="Monster race")
    size: str = Field(..., description="Monster size (Small, Medium, Large)")
    stats: MonsterStats = Field(..., description="Monster stats")
    drops: Optional[List[Drop]] = Field(None, description="Item drops")
    mvp: bool = Field(False, description="Is MVP monster")
    mvp_drops: Optional[List[Drop]] = Field(None, description="MVP drops")
    spawn_locations: Optional[List[str]] = Field(None, description="Spawn locations")
    sprite: Optional[str] = Field(None, description="Sprite reference")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1002,
                "name": "Poring",
                "level": 1,
                "element": "Water",
                "element_level": 1,
                "race": "Plant",
                "size": "Medium",
                "stats": {
                    "hp": 50,
                    "base_exp": 2,
                    "job_exp": 1,
                    "atk": 7,
                    "defense": 0,
                    "mdef": 5,
                    "str": 1,
                    "agi": 1,
                    "vit": 1,
                    "int": 0,
                    "dex": 6,
                    "luk": 30
                },
                "mvp": False,
                "drops": [
                    {"item_id": 909, "item_name": "Jellopy", "rate": 70.0}
                ],
                "spawn_locations": ["prontera", "geffen"]
            }
        }
    }
