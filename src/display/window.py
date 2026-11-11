"""animated pygame window showing the drones fly turn by turn."""

import math
import pygame
from ..models import Network, Zone, ZoneType
from ..pathfinding.scheduler import Step

WIDTH, HEIGHT, PANEL, MARGIN = 1280, 760, 300, 70
BG, CARD, LINE = (11, 15, 26), (26, 34, 54), (52, 64, 92)
TEXT, DIM, BLUE, GOLD = (232, 238, 250), (120, 134, 165), (94, 200, 255), \
    (255, 206, 84)
RING = {
    ZoneType.NORMAL: (150, 165, 195),
    ZoneType.PRIORITY: BLUE,
    ZoneType.RESTRICTED: (255, 140, 66),
    ZoneType.BLOCKED: (90, 96, 110),
}


class Visualizer:
    """draw the map and animate the planned paths."""

    def __init__(self, network: Network, paths: list[list[Step]],
                 lines: list[str]) -> None:
        """compute screen positions once."""
        self.network, self.paths, self.lines = network, paths, lines
        self.last = len(lines)
        zones = network.zones.values()
        x0, y0 = min(z.x for z in zones), min(z.y for z in zones)
        dx = max(max(z.x for z in zones) - x0, 1)
        dy = max(max(z.y for z in zones) - y0, 1)
        sx = (WIDTH - PANEL - 2 * MARGIN) / dx
        sy = min((HEIGHT - 2 * MARGIN) / dy, sx * 2)
        self.pos = {z.name: (MARGIN + (z.x - x0) * sx,
                             (HEIGHT + dy * sy) / 2 - (z.y - y0) * sy)
                    for z in zones}
        self.radius = int(max(9, min(20, min(sx, sy) / 3)))

    def run(self) -> None:
        """open the window; space pauses, arrows step, r restarts."""
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fly-in")
        self.font = pygame.font.SysFont("menlo,monospace", 14)
        clock, t, paused = pygame.time.Clock(), 0.0, False
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return pygame.quit()
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key == pygame.K_ESCAPE:
                    return pygame.quit()
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_r:
                    t = 0.0
                if event.key == pygame.K_RIGHT:
                    paused, t = True, float(min(int(t) + 1, self.last))
                if event.key == pygame.K_LEFT:
                    paused, t = True, float(max(math.ceil(t) - 1, 0))
            if not paused:
                t = min(t + clock.get_time() / 1000, float(self.last))
            clock.tick(60)
            self.draw(screen, t)
            pygame.display.flip()

    def draw(self, screen: pygame.Surface, t: float) -> None:
        """draw one frame at time t (in turns, can be fractional)."""
        screen.fill(BG)
        for link in self.network.connections:
            a, b = self.pos[link.zone_a.name], self.pos[link.zone_b.name]
            pygame.draw.line(screen, LINE, a, b, 2)
        for zone in self.network.zones.values():
            self._draw_zone(screen, zone)
        for drone, path in enumerate(self.paths, start=1):
            if self._takeoff(path) < t < path[-1][0]:
                self._draw_drone(screen, drone, *self._where(path, t))
        self._draw_panel(screen, t)

    def _draw_zone(self, screen: pygame.Surface, zone: Zone) -> None:
        """draw a zone: dark fill, ring colored by its type."""
        x, y = self.pos[zone.name]
        hub = zone.is_start or zone.is_end
        r = self.radius + (8 if hub else 0)
        try:
            fill = pygame.Color(zone.color or "gray20").lerp(BG, 0.5)
        except ValueError:
            fill = pygame.Color("gray20")
        pygame.draw.circle(screen, fill, (x, y), r)
        pygame.draw.circle(screen, GOLD if hub else RING[zone.zone_type],
                           (x, y), r, 3)
        if hub:
            label = self.font.render(zone.name, True, DIM)
            screen.blit(label, label.get_rect(midtop=(x, y + r + 6)))

    def _draw_drone(self, screen: pygame.Surface, drone: int,
                    x: float, y: float) -> None:
        """draw a small quadcopter with its number."""
        x, y = x + math.cos(drone * 2.4) * 8, y + math.sin(drone * 2.4) * 8
        color = pygame.Color(0)
        color.hsva = (drone * 47 % 360, 60, 100, 100)
        for dx, dy in ((-6, -6), (6, -6), (-6, 6), (6, 6)):
            pygame.draw.line(screen, color, (x, y), (x + dx, y + dy), 2)
            pygame.draw.circle(screen, color, (x + dx, y + dy), 3, 1)
        self._text(screen, str(drone), (x + 9, y - 20), TEXT)

    def _draw_panel(self, screen: pygame.Surface, t: float) -> None:
        """draw the side panel: progress bar, counts, keys, moves."""
        x = WIDTH - PANEL + 24
        pygame.draw.rect(screen, CARD, (WIDTH - PANEL, 0, PANEL, HEIGHT))
        bar = pygame.Rect(x, 30, int((PANEL - 48) * t / self.last), 8)
        pygame.draw.rect(screen, BLUE, bar, border_radius=4)
        turn = min(math.ceil(t), self.last)
        waiting = sum(1 for path in self.paths if self._takeoff(path) >= t)
        done = sum(1 for path in self.paths if path[-1][0] <= t)
        rows = [f"turn     {turn} / {self.last}", f"waiting  {waiting}",
                f"arrived  {done}", "", "space pause  <- -> step",
                "r restart  esc quit", ""]
        if turn > 0:
            rows += self.lines[turn - 1].split()
        for i, row in enumerate(rows[:32]):
            self._text(screen, row, (x, 60 + i * 20), BLUE if i > 6 else TEXT)

    def _text(self, screen: pygame.Surface, text: str,
              at: tuple[float, float], color: tuple[int, int, int]) -> None:
        """blit one line of text."""
        screen.blit(self.font.render(text, True, color), at)

    @staticmethod
    def _takeoff(path: list[Step]) -> int:
        """return the turn when the drone leaves the start hub."""
        return next((turn for (turn, a, _), (_, b, _) in zip(path, path[1:])
                     if a is not b), path[-1][0])

    def _where(self, path: list[Step], t: float) -> tuple[float, float]:
        """return the screen position of a drone at time t."""
        for (start, a, _), (end, b, _) in zip(path, path[1:]):
            if start <= t <= end:
                k = (t - start) / (end - start)
                (ax, ay), (bx, by) = self.pos[a.name], self.pos[b.name]
                return ax + (bx - ax) * k, ay + (by - ay) * k
        return self.pos[path[-1][1].name]

