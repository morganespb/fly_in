from enum import Enum
from typing import Optional


class ZoneType(Enum):
    """zone type: cost of moving into it"""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def move_cost(self) -> int:
        """Return how many turns a move into a zone of this type takes"""
        if self is ZoneType.RESTRICTED:
            return 2
        return 1

    @property
    def is_enterable(self) -> bool:
        """Return True if drones are allowed to enter"""
        return self is not ZoneType.BLOCKED


class Zone:
    """A named zone of the map with a limited number of drones"""

    def __init__(
        self, name: str, x: int, y: int, zone_type: ZoneType = ZoneType.NORMAL,
        color: Optional[str] = None, max_drones: int = 1, 
        is_start: bool = False, is_end: bool = False) -> None:
        
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.color: Optional[str] = color
        self.max_drones: int = max_drones
        self.is_start: bool = is_start
        self.is_end: bool = is_end

    @property
    def capacity(self) -> Optional[int]:
        """how many drones fit in the zone?"""
        if self.is_start or self.is_end:
            return None
        return self.max_drones

    @property
    def move_cost(self) -> int:
        """how many turns a move into this zone takes?"""
        return self.zone_type.move_cost

    def __repr__(self) -> str:
        """debug representation (pbp)"""
        return (
            f"Zone({self.name!r}, ({self.x}, {self.y}), "
            f"{self.zone_type.value}, max={self.max_drones})"
        )
