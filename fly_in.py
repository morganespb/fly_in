"""fly-in entry point: python3 fly_in.py <map_file>."""

import os
import sys
from src.parser.errors import ParseError
from src.parser.map_parser import MapParser
from src.pathfinding.scheduler import Scheduler
from src.simulation.engine import Simulation


def show(simulation: Simulation, lines: list[str]) -> None:
    """open the pygame window, or explain why it cannot open."""
    sys.stdout.flush()
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        from src.display.window import Visualizer
        Visualizer(simulation.network, simulation.paths, lines).run()
    except ImportError:
        print("pygame is not installed: run 'make install'", file=sys.stderr)
    except Exception as error:
        print(f"cannot open the window: {error}", file=sys.stderr)


def main(argv: list[str]) -> int:
    """parse the map, plan the drones, print the turns, show the window."""
    gui = "--no-gui" not in argv
    args = [arg for arg in argv if arg != "--no-gui"]
    if len(args) != 1:
        print("Usage: python3 fly_in.py <map_file> [--no-gui]",
              file=sys.stderr)
        return 2
    try:
        network = MapParser().parse_file(args[0])
        paths = Scheduler(network).plan_all()
        simulation = Simulation(network, paths)
        simulation.check()
    except (ParseError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    lines = simulation.lines()
    for line in lines:
        print(line)
    if gui:
        show(simulation, lines)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)

