"""animated pygame window showing the drones fly turn by turn."""

import math
import pygame
from ..models import Network, Zone, ZoneType
from ..pathfinding.scheduler import Step

WIDTH, HEIGHT, PANEL, MARGIN = 1280, 760, 320, 70
SPEED = 1.0
BG, BG2 = (11, 15, 26), (20, 27, 45)
CARD, LINE, DIM = (26, 34, 54), (52, 64, 92), (120, 134, 165)
TEXT, ACCENT, GOLD = (232, 238, 250), (94, 200, 255), (255, 206, 84)
RING = {
    ZoneType.NORMAL: (150, 165, 195),
    ZoneType.PRIORITY: (94, 200, 255),
    ZoneType.RESTRICTED: (255, 140, 66),
    ZoneType.BLOCKED: (90, 96, 110),
}
LEGEND = (("normal", ZoneType.NORMAL), ("priority", ZoneType.PRIORITY),
          ("restricted (2 turns)", ZoneType.RESTRICTED),
          ("blocked", ZoneType.BLOCKED))


class Visualizer:
    """draw the map and animate the planned paths."""

    def __init__(self, network: Network, paths: list[list[Step]],
                 lines: list[str]) -> None:
        """compute screen positions once."""
        self.network = network
        self.paths = paths
        self.lines = lines
        self.last = len(lines)
        zones = list(network.zones.values())
        min_x, min_y = min(z.x for z in zones), min(z.y for z in zones)
        span_x = max(max(z.x for z in zones) - min_x, 1)
        span_y = max(max(z.y for z in zones) - min_y, 1)
        sx = (WIDTH - PANEL - 2 * MARGIN) / span_x
        sy = (HEIGHT - 2 * MARGIN) / span_y
        sy = min(sy, sx * 2)
        off_x = (WIDTH - PANEL - span_x * sx) / 2
        off_y = (HEIGHT + span_y * sy) / 2
        self.pos = {z.name: (off_x + (z.x - min_x) * sx,
                             off_y - (z.y - min_y) * sy) for z in zones}
        scale = min(sx, sy)
        self.radius = int(max(9, min(20, scale / 3.2)))
        self.labels = scale > 110

    def run(self) -> None:
        """open the window; space pauses, arrows step, r restarts."""
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fly-in")
        self.font = pygame.font.SysFont("menlo,dejavusansmono,monospace", 14)
        self.big = pygame.font.SysFont("menlo,dejavusansmono,monospace", 30,
                                       bold=True)
        clock = pygame.time.Clock()
        t, paused = 0.0, False
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                        event.type == pygame.KEYDOWN
                        and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_r:
                        t = 0.0
                    elif event.key == pygame.K_RIGHT:
                        paused, t = True, float(min(int(t) + 1, self.last))
                    elif event.key == pygame.K_LEFT:
                        paused, t = True, float(max(math.ceil(t) - 1, 0))
            dt = clock.tick(60) / 1000
            if not paused:
                t = min(t + dt * SPEED, float(self.last))
            self.draw(screen, t)
            pygame.display.flip()

    def draw(self, screen: pygame.Surface, t: float) -> None:
        """draw one frame at time t (in turns, can be fractional)."""
        screen.fill(BG)
        for y in range(0, HEIGHT, 28):
            for x in range(0, WIDTH - PANEL, 28):
                screen.set_at((x, y), BG2)
        busy = self._busy_links(t)
        for link in self.network.connections:
            a, b = self.pos[link.zone_a.name], self.pos[link.zone_b.name]
            color = ACCENT if link.key in busy else LINE
            pygame.draw.line(screen, color, a, b,
                             1 + min(link.max_link_capacity, 4))
        for zone in self.network.zones.values():
            self._draw_zone(screen, zone)
        flying = [(d, p) for d, p in enumerate(self.paths, start=1)
                  if self._takeoff(p) < t < p[-1][0]]
        for drone, path in flying:
            px, py = self._where(path, t)
            angle = drone * 2.4
            self._draw_drone(screen, drone, px + math.cos(angle) * 8,
                             py + math.sin(angle) * 8)
        self._draw_badges(screen, t)
        self._draw_panel(screen, t, len(flying))
        self._draw_tooltip(screen)

    def _draw_zone(self, screen: pygame.Surface, zone: Zone) -> None:
        """draw a zone as a ring colored by its type."""
        x, y = self.pos[zone.name]
        r = self.radius + (8 if zone.is_start or zone.is_end else 0)
        try:
            fill = pygame.Color(zone.color or "gray20")
        except ValueError:
            fill = pygame.Color("gray20")
        fill = fill.lerp(BG, 0.55)
        ring = GOLD if zone.is_start or zone.is_end else RING[zone.zone_type]
        if zone.zone_type == ZoneType.PRIORITY or zone.is_end:
            glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*ring, 45), (r * 2, r * 2), r + 7)
            screen.blit(glow, (x - r * 2, y - r * 2))
        pygame.draw.circle(screen, fill, (x, y), r)
        pygame.draw.circle(screen, ring, (x, y), r, 3)
        if zone.zone_type == ZoneType.BLOCKED:
            d = r * 0.5
            pygame.draw.line(screen, ring, (x - d, y - d), (x + d, y + d), 3)
            pygame.draw.line(screen, ring, (x - d, y + d), (x + d, y - d), 3)
        if self.labels or zone.is_start or zone.is_end:
            label = self.font.render(zone.name, True, DIM)
            screen.blit(label, (x - label.get_width() / 2, y + r + 6))

    def _draw_drone(self, screen: pygame.Surface, drone: int,
                    x: float, y: float) -> None:
        """draw a small quadcopter with its number."""
        color = pygame.Color(0)
        color.hsva = (drone * 47 % 360, 60, 100, 100)
        for dx, dy in ((-6, -6), (6, -6), (-6, 6), (6, 6)):
            pygame.draw.line(screen, color, (x, y), (x + dx, y + dy), 2)
            pygame.draw.circle(screen, color, (x + dx, y + dy), 3, 1)
        pygame.draw.circle(screen, color, (x, y), 4)
        if len(self.paths) <= 30:
            tag = self.font.render(str(drone), True, TEXT)
            screen.blit(tag, (x + 9, y - 20))

    def _draw_badges(self, screen: pygame.Surface, t: float) -> None:
        """show how many drones wait at start and arrived at the end."""
        waiting = sum(1 for p in self.paths if self._takeoff(p) >= t)
        done = sum(1 for p in self.paths if p[-1][0] <= t)
        for zone, count in ((self.network.start, waiting),
                            (self.network.end, done)):
            x, y = self.pos[zone.name]
            text = self.font.render(str(count), True, BG)
            w = max(text.get_width() + 12, 24)
            box = pygame.Rect(0, 0, w, 22)
            box.center = (int(x), int(y - self.radius - 22))
            pygame.draw.rect(screen, GOLD, box, border_radius=11)
            screen.blit(text, text.get_rect(center=box.center))

    def _draw_panel(self, screen: pygame.Surface, t: float,
                    flying: int) -> None:
        """draw the side panel: turn, progress, stats, legend, moves."""
        left = WIDTH - PANEL
        pygame.draw.rect(screen, CARD, (left, 0, PANEL, HEIGHT))
        pygame.draw.line(screen, LINE, (left, 0), (left, HEIGHT), 2)
        x, y = left + 24, 24
        screen.blit(self.big.render("FLY-IN", True, ACCENT), (x, y))
        turn = min(math.ceil(t), self.last)
        y += 50
        self._text(screen, f"turn {turn} / {self.last}", (x, y), TEXT)
        bar = pygame.Rect(x, y + 26, PANEL - 48, 8)
        pygame.draw.rect(screen, LINE, bar, border_radius=4)
        bar.width = int(bar.width * t / max(self.last, 1))
        pygame.draw.rect(screen, ACCENT, bar, border_radius=4)
        done = sum(1 for p in self.paths if p[-1][0] <= t)
        stats = (("drones", len(self.paths)), ("flying", flying),
                 ("arrived", done))
        y += 56
        for name, value in stats:
            self._text(screen, f"{name:<10}{value:>6}", (x, y), DIM)
            y += 22
        y += 16
        for name, zone_type in LEGEND:
            pygame.draw.circle(screen, RING[zone_type], (x + 7, y + 9), 7, 3)
            self._text(screen, name, (x + 24, y), DIM)
            y += 24
        y += 16
        self._text(screen, "moves this turn", (x, y), TEXT)
        y += 26
        moves = self.lines[turn - 1].split() if turn > 0 else []
        room = (HEIGHT - 70 - y) // 20
        for move in moves[:room]:
            self._text(screen, move, (x, y), ACCENT)
            y += 20
        if len(moves) > room:
            self._text(screen, f"+{len(moves) - room} more", (x, y), DIM)
        keys = "space pause  <- -> step  r restart"
        self._text(screen, keys, (x, HEIGHT - 36), DIM)

    def _draw_tooltip(self, screen: pygame.Surface) -> None:
        """show the zone name under the mouse."""
        mx, my = pygame.mouse.get_pos()
        for name, (x, y) in self.pos.items():
            if math.hypot(mx - x, my - y) <= self.radius + 4:
                text = self.font.render(name, True, TEXT)
                box = text.get_rect(topleft=(mx + 14, my + 10)).inflate(12, 8)
                pygame.draw.rect(screen, CARD, box, border_radius=6)
                pygame.draw.rect(screen, LINE, box, 1, border_radius=6)
                screen.blit(text, (mx + 14, my + 10))
                return

    def _text(self, screen: pygame.Surface, text: str,
              at: tuple[float, float], color: tuple[int, int, int]) -> None:
        """blit one line of text."""
        screen.blit(self.font.render(text, True, color), at)

    def _busy_links(self, t: float) -> set[frozenset[str]]:
        """return the keys of the links a drone is flying on."""
        busy = set()
        for path in self.paths:
            for (start, a, _), (end, b, _) in zip(path, path[1:]):
                if start < t < end and a is not b:
                    busy.add(frozenset((a.name, b.name)))
        return busy

    @staticmethod
    def _takeoff(path: list[Step]) -> int:
        """return the turn when the drone leaves the start hub."""
        moving = [turn for (turn, zone, _), (_, nxt, _) in zip(path, path[1:])
                  if nxt is not zone]
        return moving[0] if moving else path[-1][0]

    def _where(self, path: list[Step], t: float) -> tuple[float, float]:
        """return the screen position of a drone at time t."""
        for (start, origin, _), (arrive, zone, _) in zip(path, path[1:]):
            if start <= t <= arrive:
                k = (t - start) / (arrive - start)
                k = k * k * (3 - 2 * k)
                (ax, ay), (bx, by) = self.pos[origin.name], self.pos[zone.name]
                return ax + (bx - ax) * k, ay + (by - ay) * k
        return self.pos[path[-1][1].name]
