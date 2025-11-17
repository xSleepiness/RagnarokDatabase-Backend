"""Item data models"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ItemStats(BaseModel):
    """Item statistics"""
    atk: Optional[int] = Field(None, description="Attack power")
    matk: Optional[int] = Field(None, description="Magic attack power")
    defense: Optional[int] = Field(None, description="Defense")
    weight: Optional[int] = Field(None, description="Weight")
    slots: Optional[int] = Field(None, description="Number of slots")


class Item(BaseModel):
    """Ragnarok Online Item model"""
    id: int = Field(..., description="Unique item ID")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    type: str = Field(..., description="Item type (weapon, armor, consumable, etc.)")
    subtype: Optional[str] = Field(None, description="Item subtype")
    buy_price: Optional[int] = Field(None, description="NPC buy price")
    sell_price: Optional[int] = Field(None, description="NPC sell price")
    stats: Optional[ItemStats] = Field(None, description="Item stats")
    required_level: Optional[int] = Field(None, description="Required level to use")
    required_job: Optional[List[str]] = Field(None, description="Required job classes")
    gender: Optional[str] = Field(None, description="Gender restriction")
    location: Optional[str] = Field(None, description="Equipment location")
    sprite: Optional[str] = Field(None, description="Sprite/icon reference")
    script: Optional[str] = Field(None, description="Script to execute when the item is used/equipped")
    equip_script: Optional[str] = Field(None, description="Script to execute when the item is equipped")
    unequip_script: Optional[str] = Field(None, description="Script to execute when the item is unequipped")
    image_url: Optional[str] = Field(None, description="URL to item image")
    collection_image_url: Optional[str] = Field(None, description="URL to collection image")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1201,
                "name": "Knife",
                "description": "A basic dagger",
                "type": "weapon",
                "subtype": "dagger",
                "buy_price": 50,
                "sell_price": 25,
                "stats": {
                    "atk": 17,
                    "weight": 40,
                    "slots": 3
                },
                "required_level": 1,
                "required_job": ["Novice", "Swordman", "Thief"],
                "sprite": "knife.png",
                "image_url": "/static/images/item/1201.png",
                "collection_image_url": "/static/images/collection/1201.png"
            }
        }
    }
