"""parser for map files"""

import re
from ..models import Connection, Network, Zone, ZoneType
from .errors import ParseError

INT_RE = re.compile(r"^[+-]?\d+$")
ZONE_PREFIXES = ("start_hub", "end_hub", "hub")
ZONE_TAGS = ("zone", "color", "max_drones")
CONNECTION_TAGS = ("max_link_capacity",)


class MapParser:
    """Turn the text of a map file into a class object `Network`

    Usage:
        network = MapParser().parse_file("maps/easy/01_linear_path.txt")"""

    def __init__(self) -> None:
        self._network: Network | None = None
        self._line_no: int = 0
        self._line: str = ""

    def parse_file(self, path: str) -> Network:
        """Read the file at ``path`` and parse it.
        raises ParseError: If the file cannot be read or is invalid"""

        try:
            with open(path, "r", encoding="utf-8") as file:
                lines = file.read().splitlines()
        except FileNotFoundError:
            raise ParseError(f"cannot open '{path}': no such file")
        except IsADirectoryError:
            raise ParseError(f"cannot open '{path}': it is a directory")
        except PermissionError:
            raise ParseError(f"cannot open '{path}': permission denied")
        except UnicodeDecodeError:
            raise ParseError(f"cannot read '{path}': not a UTF-8 text file")
        except OSError as error:
            raise ParseError(f"cannot read '{path}': {error.strerror}")
        return self.parse_lines(lines)

    def parse_lines(self, lines: list[str]) -> Network:
        """parse the lines of a map"""

        self._network = None
        for index, raw in enumerate(lines, start=1):
            self._line_no = index
            self._line = raw
            text = raw.strip()
            if not text or text.startswith("#"):
                continue
            self._parse_line(text)
        return self._finish()

    def _error(self, message: str) -> ParseError:
        """build a ParseError for the line being parsed"""
        return ParseError(message, self._line_no, self._line)

    def _parse_line(self, text: str) -> None:
        """dispatch one meaningful line on its ``key:`` prefix."""
        if ":" not in text:
            raise self._error(
                "expected '<key>: <value>' (e.g. 'hub: name 0 0')"
            )
        key, _, value = text.partition(":")
        key = key.strip()
        value = value.strip()
        if self._network is None:
            if key != "nb_drones":
                raise self._error(
                    "the first line must be 'nb_drones: <positive_integer>'"
                )
            self._network = Network(self._parse_nb_drones(value))
            return
        if key == "nb_drones":
            raise self._error("nb_drones is defined more than once")
        if key in ZONE_PREFIXES:
            self._parse_zone(key, value, self._network)
        elif key == "connection":
            self._parse_connection(value, self._network)
        else:
            raise self._error(
                f"unknown line type '{key}' (expected start_hub, end_hub, "
                "hub or connection)"
            )

    def _parse_positive_int(self, value: str, what: str) -> int:
        """return ``value`` as an integer > 0, or raise a ParseError."""
        if not INT_RE.match(value):
            raise self._error(f"{what} must be a positive integer, "
                              f"got '{value}'")
        number = int(value)
        if number <= 0:
            raise self._error(f"{what} must be a positive integer, "
                              f"got {number}")
        return number

    def _parse_nb_drones(self, value: str) -> int:
        """parse the value of the nb_drones line."""
        if not value:
            raise self._error("nb_drones has no value")
        return self._parse_positive_int(value, "nb_drones")

    def _split_metadata(
        self, value: str, allowed: tuple[str, ...]
    ) -> tuple[str, dict[str, str]]:
        """split ``body [k=v ...]`` into the body and a tag dict"""
        opens = value.count("[")
        closes = value.count("]")
        if opens == 0 and closes == 0:
            return value, {}
        if opens != 1 or closes != 1 or not value.endswith("]"):
            raise self._error(
                "malformed metadata: use one '[...]' block at the end "
                "of the line"
            )
        body, _, inside = value[:-1].partition("[")
        tags: dict[str, str] = {}
        for item in inside.split():
            name, sep, tag_value = item.partition("=")
            if not sep or not name or not tag_value:
                raise self._error(
                    f"malformed metadata '{item}': expected key=value"
                )
            if name not in allowed:
                raise self._error(
                    f"unknown metadata '{name}' (allowed here: "
                    f"{', '.join(allowed)})"
                )
            if name in tags:
                raise self._error(f"metadata '{name}' is given twice")
            tags[name] = tag_value
        return body.strip(), tags

    def _check_zone_name(self, name: str) -> None:
        """reject names that the connection syntax cannot handle"""
        if "-" in name:
            raise self._error(
                f"invalid zone name '{name}': dashes are not allowed"
            )

    def _parse_zone(self, kind: str, value: str, network: Network) -> None:
        """parse a ``start_hub:``, ``end_hub:`` or ``hub:`` line."""
        body, tags = self._split_metadata(value, ZONE_TAGS)
        parts = body.split()
        if len(parts) != 3:
            raise self._error(
                f"{kind} needs exactly '<name> <x> <y>', got {len(parts)} "
                "field(s)"
            )
        name, raw_x, raw_y = parts
        self._check_zone_name(name)
        if name in network.zones:
            raise self._error(f"zone '{name}' is already defined")
        for axis, raw in (("x", raw_x), ("y", raw_y)):
            if not INT_RE.match(raw):
                raise self._error(
                    f"{axis} coordinate of '{name}' must be an integer, "
                    f"got '{raw}'"
                )
        zone_type = ZoneType.NORMAL
        if "zone" in tags:
            try:
                zone_type = ZoneType(tags["zone"])
            except ValueError:
                raise self._error(
                    f"unknown zone type '{tags['zone']}' (expected normal, "
                    "blocked, restricted or priority)"
                )
        max_drones = 1
        if "max_drones" in tags:
            max_drones = self._parse_positive_int(
                tags["max_drones"], "max_drones"
            )
        is_start = kind == "start_hub"
        is_end = kind == "end_hub"
        if is_start and network.has_start:
            raise self._error("there is more than one start_hub")
        if is_end and network.has_end:
            raise self._error("there is more than one end_hub")
        if (is_start or is_end) and zone_type is ZoneType.BLOCKED:
            raise self._error(f"{kind} '{name}' cannot be a blocked zone")
        network.add_zone(Zone(
            name, int(raw_x), int(raw_y), zone_type, tags.get("color"),
            max_drones, is_start, is_end,
        ))

    def _parse_connection(self, value: str, network: Network) -> None:
        """Parse a ``connection: a-b [max_link_capacity=N]`` line."""
        body, tags = self._split_metadata(value, CONNECTION_TAGS)
        parts = body.split()
        if len(parts) != 1:
            raise self._error(
                "connection must be '<zone1>-<zone2>' with no spaces"
            )
        names = parts[0].split("-")
        if len(names) != 2 or not names[0] or not names[1]:
            raise self._error(
                f"invalid connection '{parts[0]}': expected <zone1>-<zone2>"
            )
        name_a, name_b = names
        for name in (name_a, name_b):
            if name not in network.zones:
                raise self._error(
                    f"connection uses unknown zone '{name}' (zones must be "
                    "defined before their connections)"
                )
        if name_a == name_b:
            raise self._error(f"zone '{name_a}' cannot connect to itself")
        if network.has_connection(name_a, name_b):
            raise self._error(
                f"duplicate connection '{name_a}-{name_b}' "
                "(a-b and b-a are the same link)"
            )
        capacity = 1
        if "max_link_capacity" in tags:
            capacity = self._parse_positive_int(
                tags["max_link_capacity"], "max_link_capacity"
            )
        network.add_connection(Connection(
            network.zones[name_a], network.zones[name_b], capacity
        ))

    def _finish(self) -> Network:
        """Run the whole-file checks and return the network."""
        if self._network is None:
            raise ParseError("the map is empty: 'nb_drones: <n>' is missing")
        network = self._network
        if not network.has_start:
            raise ParseError("the map has no start_hub")
        if not network.has_end:
            raise ParseError("the map has no end_hub")
        return network
