import pygame
from pygame import gfxdraw

from objects import Color, Planet, GameState

WHITE: Color = (255, 255, 255)
TEXT: Color = (235, 240, 255)
TEXT_DIM: Color = (165, 175, 200)
BG: Color = (6, 8, 18)  # near-black deep blue
HUD_LINE_HEIGHT = 22
HUD_FONT_SIZE = 16
HUD_PAD = 10

# Cache of pre-rendered glow halos keyed by (radius bucket, color).
# Halos are circular alpha-decay sprites blitted with BLEND_RGB_ADD.
_glow_cache: dict[tuple[int, Color], pygame.Surface] = {}
_font_cache: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    cached = _font_cache.get(size)
    if cached is not None:
        return cached
    # Prefer a monospace face for the HUD so columns line up; fall back gracefully.
    for name in ('Menlo', 'Consolas', 'DejaVu Sans Mono', 'Courier New', 'monospace'):
        try:
            f = pygame.font.SysFont(name, size, bold=True)
            _font_cache[size] = f
            return f
        except Exception:
            continue
    f = pygame.font.SysFont(None, size, bold=True)
    _font_cache[size] = f
    return f


def _get_glow(radius: int, color: Color) -> pygame.Surface:
    # Bucket radius so the cache doesn't explode under continuous zoom.
    bucket = max(2, ((radius + 1) // 2) * 2)
    key = (bucket, color)
    cached = _glow_cache.get(key)
    if cached is not None:
        return cached

    size = bucket * 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    max_r = bucket * 2
    for r in range(max_r, 0, -1):
        t = r / max_r
        alpha = int(22 * (1 - t) ** 2)
        if alpha <= 0:
            continue
        gfxdraw.filled_circle(surf, center, center, r, (*color, alpha))
    _glow_cache[key] = surf
    return surf


def draw(state: GameState, screen: pygame.Surface):
    screen.fill(BG)
    _draw_hud(state, screen)
    border = 1 if state.debug else 0

    screen_w, screen_h = screen.get_size()

    # Trails first so planet bodies sit on top.
    for planet in state.planets:
        _draw_trail(state, planet, screen, screen_w, screen_h)

    for planet in state.planets:
        _draw_planet(state, planet, border, screen, screen_w, screen_h)
        if state.debug:
            describe_planet(state, planet, screen)

    if state.pending_planet is not None:
        _draw_planet(state, state.pending_planet.to_planet(), border, screen, screen_w, screen_h)

    pygame.display.flip()


def _draw_hud(state: GameState, screen: pygame.Surface):
    # Fixed-width grid: every cell is `{key:>K}  {action:<A}`.
    # Keys right-aligned so single-char keys hug their action label; pad empty cells.
    K, A = 6, 16
    cell_w = K + 2 + A  # 24
    gutter = '  '

    grid: list[list[tuple[str, str]]] = [
        [('q', 'quit'),          ('p', 'pause'),       ('r', 'reset'),         ('d', 'debug')],
        [('g', 'fixed toggle'),  ('c', 'center place'),('x', 'delete @cursor'),('', '')],
        [('L-drag', 'place'),    ('R-drag', 'pan'),    ('wheel', 'zoom'),      ('', '')],
        [('k/j', 'radius'),      ('f/s', 'time warp'), ('e/w', 'density'),     ('[/]', 'trail length')],
        [('1', 'empty'),         ('2', 'Sun+Earth'),   ('3', 'Solar system'),  ('4', 'Binary star')],
        [('5', 'Lagrange 3-body'), ('6', 'Chaotic swarm'), ('7', 'Jupiter system'), ('', '')],
    ]

    def _cell(key: str, action: str) -> str:
        if not key and not action:
            return ' ' * cell_w
        return f'{key:>{K}}  {action:<{A}}'

    legend_lines = [gutter.join(_cell(k, a) for k, a in row) for row in grid]

    # Status: each field gets a fixed-width slot so the row doesn't shimmy as values change.
    status = (
        f'radius {state.radius:<5}'
        f'warp {state.time_warp:<5}'
        f'density {state.new_planet_density:<8}'
        f'trail {state.trail_length:<7}'
        f'fixed {str(state.new_planet_fixed_position):<6}'
        f'zoom {state.zoom:>5.2f}x   '
        f'planets {len(state.planets)}'
    )

    font = _font(HUD_FONT_SIZE)
    rendered_legend = [font.render(t, True, TEXT_DIM) for t in legend_lines]
    rendered_status = font.render(status, True, TEXT)
    separator = font.render('-' * (len(legend_lines[0])), True, (60, 70, 95))
    all_surfs = rendered_legend + [separator, rendered_status]

    panel_w = max(s.get_width() for s in all_surfs) + 2 * HUD_PAD
    panel_h = len(all_surfs) * HUD_LINE_HEIGHT + 2 * HUD_PAD

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))
    pygame.draw.rect(panel, (90, 110, 160, 220), panel.get_rect(), width=1)
    screen.blit(panel, (10, 10))

    for i, surf in enumerate(all_surfs):
        screen.blit(surf, (10 + HUD_PAD, 10 + HUD_PAD + i * HUD_LINE_HEIGHT))


_TRAIL_MAX_RENDER_SEGMENTS = 2000


def _draw_trail(state: GameState, planet: Planet, screen: pygame.Surface, sw: int, sh: int):
    track = planet.track
    n = len(track)
    if n < 2:
        return

    color = planet.color
    bg = BG

    # Decimate: regardless of stored length, render at most ~2000 segments per
    # trail. Stride increases as trail grows so render cost stays roughly flat.
    points = list(track)  # deque indexing is O(n); snapshot once
    stride = max(1, n // _TRAIL_MAX_RENDER_SEGMENTS)

    # Per-segment aalines, color-mixed from bg (old) toward planet color (new),
    # giving a fading-gradient look without needing alpha-capable line primitives.
    prev = state.world_to_screen(*points[0])
    inv = 1.0 / (n - 1)
    for i in range(stride, n, stride):
        cur = state.world_to_screen(*points[i])
        # Cheap off-screen cull for both endpoints.
        if (
            (prev[0] < 0 and cur[0] < 0)
            or (prev[0] > sw and cur[0] > sw)
            or (prev[1] < 0 and cur[1] < 0)
            or (prev[1] > sh and cur[1] > sh)
        ):
            prev = cur
            continue
        t = i * inv  # 0 at oldest segment, ~1 at newest
        r = int(bg[0] + (color[0] - bg[0]) * t)
        g = int(bg[1] + (color[1] - bg[1]) * t)
        b = int(bg[2] + (color[2] - bg[2]) * t)
        pygame.draw.aaline(screen, (r, g, b), prev, cur)
        prev = cur


def _draw_planet(state: GameState, planet: Planet, border: int, screen: pygame.Surface, sw: int, sh: int):
    sx, sy = state.world_to_screen(planet.x, planet.y)
    sr = max(1, int(planet.radius * state.zoom))

    # Off-screen cull (account for glow halo extent ~ sr*2).
    halo_extent = sr * 2
    if sx + halo_extent < 0 or sx - halo_extent > sw or sy + halo_extent < 0 or sy - halo_extent > sh:
        return

    color = planet.color

    # Glow halo (additive).
    glow = _get_glow(sr, color)
    gw, gh = glow.get_size()
    screen.blit(glow, (int(sx) - gw // 2, int(sy) - gh // 2), special_flags=pygame.BLEND_RGB_ADD)

    isx, isy = int(sx), int(sy)
    if border:
        gfxdraw.aacircle(screen, isx, isy, sr, color)
    else:
        gfxdraw.filled_circle(screen, isx, isy, sr, color)
        gfxdraw.aacircle(screen, isx, isy, sr, color)

    # Velocity vector (dim line) drawn forward in direction of motion.
    end_wx = planet.x + planet.velocity[0] * state.velocity_input_scale
    end_wy = planet.y + planet.velocity[1] * state.velocity_input_scale
    end_sx, end_sy = state.world_to_screen(end_wx, end_wy)
    pygame.draw.aaline(screen, (170, 175, 195), (sx, sy), (end_sx, end_sy))


def describe_planet(state: GameState, planet: Planet, screen: pygame.Surface):
    text: str = (
        f'PLANET'
        f' fixed: {planet.fixed_position},'
        f' coord: ({planet.x:.1f}, {planet.y:.1f}),'
        f' mass: {planet.mass:.3e},'
        f' v: ({planet.velocity[0]:.3f}, {planet.velocity[1]:.3f})'
    )
    sx, sy = state.world_to_screen(planet.x, planet.y)
    write_text(sx, sy, text, screen)


def write_text(x: float, y: float, text: str, screen: pygame.Surface, size: int = 13, color: Color = TEXT):
    screen.blit(
        source=_font(size).render(text, True, color),
        dest=(x, y),
    )
