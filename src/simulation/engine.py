"""replay the planned paths turn by turn."""

from collections import Counter
from ..models import Network
from ..pathfinding.scheduler import Step


class Simulation:
    """turn planned paths into output lines and check every rule."""

    def __init__(self, network: Network, paths: list[list[Step]]) -> None:
        """keep the paths, the last arrival gives the number of turns."""
        self.network = network
        self.paths = paths
        self.nb_turns = max(path[-1][0] for path in paths)

    def lines(self) -> list[str]:
        """return one line per turn, like 'D1-roof1 D2-corridorA'."""
        lines = []
        for turn in range(1, self.nb_turns + 1):
            moves = []
            for drone, path in enumerate(self.paths, start=1):
                label = self._label(path, turn)
                if label is not None:
                    moves.append(f"D{drone}-{label}")
            lines.append(" ".join(moves))
        return lines

    def check(self) -> None:
        """raise ValueError if a turn breaks a zone or link rule."""
        for turn in range(1, self.nb_turns + 1):
            zones: Counter[str] = Counter()
            links: Counter[str] = Counter()
            for path in self.paths:
                for (start, _, _), (arrive, zone, link) in zip(path, path[1:]):
                    if not start < turn <= arrive:
                        continue
                    if not zone.zone_type.is_enterable:
                        raise ValueError(f"turn {turn}: {zone.name} blocked")
                    if link is not None:
                        links[link.name] += 1
                        if links[link.name] > link.max_link_capacity:
                            raise ValueError(f"turn {turn}: {link.name} full")
                    cap = zone.capacity
                    if turn == arrive and cap is not None:
                        zones[zone.name] += 1
                        if zones[zone.name] > cap:
                            raise ValueError(f"turn {turn}: {zone.name} full")

    @staticmethod
    def _label(path: list[Step], turn: int) -> str | None:
        """name where the drone goes this turn, None if it does not move."""
        for (start, _, _), (arrive, zone, link) in zip(path, path[1:]):
            if link is not None and start < turn <= arrive:
                return zone.name if turn == arrive else link.name
        return None
