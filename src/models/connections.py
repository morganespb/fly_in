"""bidirectional connections / edges of the network"""

from .zones import Zone


class Connection:
    """two-way link between two zones"""

    def __init__(
        self, zone_a: Zone, zone_b: Zone, max_link_capacity: int = 1) -> None:

        """create connection between two distinct zones"""
        self.zone_a: Zone = zone_a
        self.zone_b: Zone = zone_b
        self.max_link_capacity: int = max_link_capacity

    @property
    def key(self) -> frozenset[str]:
        """no order keys, so that a-b and b-a are equal."""
        return frozenset((self.zone_a.name, self.zone_b.name))
        
    @property
    def name(self) -> str:
        """gives the name used in the output : `roof1-roof2` """
        return f"{self.zone_a.name}-{self.zone_b.name}"

    def other(self, zone: Zone) -> Zone:
        """return the opposite zone"""
        if zone is self.zone_a:
            return self.zone_b
        if zone is self.zone_b:
            return self.zone_a
        raise ValueError(f"{zone.name} is not an end of {self.name}")

    def __repr__(self) -> str:
        """return a short debug representation."""
        return f"Connection({self.name!r}, cap={self.max_link_capacity})"
