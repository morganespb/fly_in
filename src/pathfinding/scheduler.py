"""plan every drone with a space-time a* and a reservation table."""

import heapq
import itertools
from collections import Counter

from ..models import Connection, Network, Zone, ZoneType
from .pathfinder import DistanceMap

# one step of a path: (turn, zone reached, link used or None if waiting)
Step = tuple[int, Zone, Connection | None]


class ReservationTable:
    """count drones per zone and per link at each turn."""

    def __init__(self) -> None:
        """start with nothing booked."""
        self.zones: Counter[tuple[int, str]] = Counter()
        self.links: Counter[tuple[int, frozenset[str]]] = Counter()

    def zone_free(self, zone: Zone, turn: int) -> bool:
        """tell if one more drone fits in zone at this turn."""
        cap = zone.capacity
        return cap is None or self.zones[(turn, zone.name)] < cap

    def link_free(self, link: Connection, turn: int) -> bool:
        """tell if one more drone fits on link at this turn."""
        return self.links[(turn, link.key)] < link.max_link_capacity

    def reserve(self, path: list[Step]) -> None:
        """book every zone and link used by path."""
        for (turn, _, _), (arrive, zone, link) in zip(path, path[1:]):
            if link is not None:
                for t in range(turn + 1, arrive + 1):
                    self.links[(t, link.key)] += 1
            if zone.capacity is not None:
                self.zones[(arrive, zone.name)] += 1


class Scheduler:
    """give each drone, one after another, its earliest free path."""

    def __init__(self, network: Network) -> None:
        """prepare the distances and an empty reservation table."""
        self.network = network
        self.dist = DistanceMap(network)
        self.table = ReservationTable()

    def plan_all(self) -> list[list[Step]]:
        """return one path per drone, D1 first."""
        if self.dist.get(self.network.start) is None:
            raise ValueError("the end hub cannot be reached from the start")
        paths = []
        for _ in range(self.network.nb_drones):
            path = self._plan_one()
            self.table.reserve(path)
            paths.append(path)
        return paths

    def _plan_one(self) -> list[Step]:
        """run the a* for one drone over (zone, turn) states."""
        start = self.network.start
        tie = itertools.count()
        first: list[Step] = [(0, start, None)]
        # heap item: (turn + turns left, penalty, tie-break, path)
        queue = [(self.dist.turns[start.name], 0, next(tie), first)]
        seen: set[tuple[str, int]] = set()
        while queue:
            _, penalty, _, path = heapq.heappop(queue)
            turn, zone, _ = path[-1]
            if zone.is_end:
                return path
            for nxt, link, arrive, extra in self._moves(zone, turn):
                if (nxt.name, arrive) in seen:
                    continue
                seen.add((nxt.name, arrive))
                guess = arrive + self.dist.turns[nxt.name]
                step: Step = (arrive, nxt, link)
                heapq.heappush(
                    queue, (guess, penalty + extra, next(tie), path + [step])
                )
        raise ValueError("no path found")

    def _moves(
        self, zone: Zone, turn: int
    ) -> list[tuple[Zone, Connection | None, int, int]]:
        """list legal moves as (zone, link, arrival turn, penalty)."""
        moves: list[tuple[Zone, Connection | None, int, int]] = []
        if self.table.zone_free(zone, turn + 1):
            moves.append((zone, None, turn + 1, 1))
        for nxt, link in self.network.neighbours(zone):
            if nxt.is_start or self.dist.get(nxt) is None:
                continue
            arrive = turn + nxt.move_cost
            trip = range(turn + 1, arrive + 1)
            if not all(self.table.link_free(link, t) for t in trip):
                continue
            if not self.table.zone_free(nxt, arrive):
                continue
            penalty = 0 if nxt.zone_type is ZoneType.PRIORITY else 1
            moves.append((nxt, link, arrive, penalty))
        return moves
