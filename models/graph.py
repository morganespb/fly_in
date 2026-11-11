"""network graph: zones, connections and adjacency lists."""

from .connections import Connection
from .zones import Zone


class Network:
    """The whole map: every zone and connection, plus the drone count.

        nb_drones: how many drones start on the start hub?
        zones: every zone, by name, in file order?
        connections: every connection, in file order?"""

    def __init__(self, nb_drones: int) -> None:
        """create an empty network for ``nb_drones`` drones."""
        self.nb_drones: int = nb_drones
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self._adjacency: dict[str, list[tuple[Zone, Connection]]] = {}
        self._by_key: dict[frozenset[str], Connection] = {}
        self._start: Zone | None = None
        self._end: Zone | None = None

    @property
    def start(self) -> Zone:
        """start hub"""
        if self._start is None:
            raise ValueError("the network has no start hub")
        return self._start

    @property
    def end(self) -> Zone:
        """end hub"""
        if self._end is None:
            raise ValueError("the network has no end hub")
        return self._end

    @property
    def has_start(self) -> bool:
        """True once a start hub was added"""
        return self._start is not None

    @property
    def has_end(self) -> bool:
        """True once an end hub was added"""
        return self._end is not None

    def add_zone(self, zone: Zone) -> None:
        """add a zone, caller checks that its name is new."""
        self.zones[zone.name] = zone
        self._adjacency[zone.name] = []
        if zone.is_start:
            self._start = zone
        if zone.is_end:
            self._end = zone

    def add_connection(self, connection: Connection) -> None:
        """add a connection, caller checks that it is new."""
        self.connections.append(connection)
        self._by_key[connection.key] = connection
        a, b = connection.zone_a, connection.zone_b
        self._adjacency[a.name].append((b, connection))
        self._adjacency[b.name].append((a, connection))

    def has_connection(self, name_a: str, name_b: str) -> bool:
        """True if the two zones are already linked"""
        return frozenset((name_a, name_b)) in self._by_key

    def get_connection(self, name_a: str, name_b: str) -> Connection:
        """Return the connection between two zones"""
        return self._by_key[frozenset((name_a, name_b))]

    def neighbours(self, zone: Zone) -> list[tuple[Zone, Connection]]:
        """Return every (neighbour zone, connection) pair of a zone"""
        return list(self._adjacency[zone.name])

    def __repr__(self) -> str:
        """debug representation"""
        return (
            f"Network({self.nb_drones} drones, {len(self.zones)} zones, "
            f"{len(self.connections)} connections)"
        )
