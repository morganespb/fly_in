"""Distances to the end hub, used as the A* heuristic."""

import heapq
from ..models import Network, Zone


class DistanceMap:
    """Shortest number of turns from every zone to the end hub.

    It is a Dijkstra run backwards from the end hub. Entering a zone
    costs its ``move_cost`` (2 for restricted), blocked zones are
    never entered. The result ignores the other drones, so it is a
    lower bound: an admissible heuristic for the space-time A*.
    """

    def __init__(self, network: Network) -> None:
        """compute distance of every zone to the end hub"""
        self.network: Network = network
        self.turns: dict[str, int] = {}
        self._compute()

    def _compute(self) -> None:
        """run Dijkstra from the end hub following links backwards"""
        end = self.network.end
        self.turns[end.name] = 0
        queue: list[tuple[int, str]] = [(0, end.name)]
        while queue:
            dist, name = heapq.heappop(queue)
            if dist > self.turns[name]:
                continue
            zone = self.network.zones[name]
            for neighbour, _ in self.network.neighbours(zone):
                if not neighbour.zone_type.is_enterable:
                    continue
                # moving neighbour -> zone costs the cost of entering zone
                new = dist + zone.move_cost
                if new < self.turns.get(neighbour.name, new + 1):
                    self.turns[neighbour.name] = new
                    heapq.heappush(queue, (new, neighbour.name))

    def get(self, zone: Zone) -> int | None:
        """return the turns from ``zone`` to the end and None if unreachable."""
        return self.turns.get(zone.name)
