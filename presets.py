"""Starter configurations for the simulator.

Each preset takes the current GameState (so we can preserve unrelated settings
like trail length / time warp / radius) and returns a fresh state with the
preset's bodies installed and the camera reset.

Orbital velocities are computed from `state.gravitational_constant` and the
chosen central mass so circular orbits stay circular at any tuning of G.
"""

import math
import random

from objects import GameState, Planet


def _empty(state: GameState) -> GameState:
    return GameState(
        # Carry over UX-only state so a preset switch doesn't fight the user.
        trail_length=state.trail_length,
        time_warp=state.time_warp,
        radius=state.radius,
        new_planet_density=state.new_planet_density,
        new_planet_fixed_position=state.new_planet_fixed_position,
        # Reset view: presets are centered at (1000, 500) which is screen center at default zoom.
        camera_x=0.0,
        camera_y=0.0,
        zoom=1.0,
    )


def empty(state: GameState) -> GameState:
    return _empty(state)


def sun_earth(state: GameState) -> GameState:
    """Sun + Earth with real masses (M_SUN, M_EARTH) and densities. Same G
    calibration as `solar_system` so Earth's orbital period stays ~30 sim-sec."""
    gs = _empty(state)
    gs = gs.copy(gravitational_constant=7.4e-26, softening=2.0)
    cx, cy = 1000, 500
    sun = Planet(
        x=cx, y=cy, radius=40, mass=M_SUN, density=D_SUN,
        fixed_position=True, color=(255, 220, 110),
    )
    gs = gs.with_append_planet(sun)
    r = 150
    v = _v_circ_softened(gs.gravitational_constant, gs.softening, sun.mass, r)
    gs = gs.with_append_planet(Planet(
        x=cx + r, y=cy, radius=8, mass=M_EARTH, density=D_EARTH,
        velocity=(0, v), color=(110, 180, 240),
    ))
    return gs


def _v_circ_softened(G: float, eps: float, M: float, r: float) -> float:
    """Circular orbital speed accounting for Plummer softening (state.softening)."""
    return math.sqrt(G * M * r * r / (r * r + eps * eps) ** 1.5)


def _density_for_mass(mass: float, radius: float) -> float:
    return mass / (math.pi * radius * radius)


# --- Real Solar System data (SI: kg for mass, kg/m^3 for density) -----------
M_SUN     = 1.989e30
M_MERCURY = 3.301e23
M_VENUS   = 4.867e24
M_EARTH   = 5.972e24
M_MARS    = 6.417e23
M_JUPITER = 1.898e27
M_SATURN  = 5.683e26
M_URANUS  = 8.681e25
M_NEPTUNE = 1.024e26

D_SUN     = 1408
D_MERCURY = 5429
D_VENUS   = 5243
D_EARTH   = 5514
D_MARS    = 3934
D_JUPITER = 1326
D_SATURN  = 687
D_URANUS  = 1271
D_NEPTUNE = 1638

M_IO       = 8.93e22
M_EUROPA   = 4.80e22
M_GANYMEDE = 1.482e23
M_CALLISTO = 1.076e23
M_TITAN    = 1.345e23
M_RHEA     = 2.306e21
M_TITANIA  = 3.40e21
M_OBERON   = 3.08e21
M_TRITON   = 2.14e22
D_IO       = 3528
D_EUROPA   = 3013
D_GANYMEDE = 1936
D_CALLISTO = 1834
D_TITAN    = 1880
D_RHEA     = 1236
D_TITANIA  = 1711
D_OBERON   = 1630
D_TRITON   = 2061


def solar_system(state: GameState) -> GameState:
    """Sun + 8 planets with **real masses and real densities** (SI kg, kg/m^3).

    Visible body radii are exaggerated for readability — at strict real scale
    the planets would be sub-pixel against orbital distances. Orbital radii
    are compressed for screen fit but ratios are roughly real (Mercury 0.39,
    Venus 0.72, Earth 1.0, Mars 1.52, Jupiter 5.2, Saturn 9.5, Uranus 19,
    Neptune 30 — Earth scaled to ~150 px, outer planets clamped to fit).

    `state.gravitational_constant` is overridden to a value that gives Earth a
    visible orbital period at the chosen length scale. With real masses and a
    naive G it would either be invisibly slow or absurdly fast; tuning G is the
    standard way to project a real n-body system into a unit-arbitrary sim.
    """
    gs = _empty(state)
    # Use REAL AU * 150 px/AU for all orbital radii. At zoom=0.2 the full
    # outer system (Neptune at sun + 4515 px world) is on-screen; user can
    # wheel-zoom in to see the inner planets and moons clearly.
    zoom = 0.20
    cx, cy = 1000, 500
    sw, sh = state.universe_bottom_right
    # G calibrated so Earth's orbital period ~30 sim-sec at r_earth=150 px:
    #   v_earth² = G*M_SUN/r, T = 2π·r/v -> G = v²r/M_SUN ≈ 7.4e-26 with T=30.
    gs = gs.copy(
        time_warp=2, trail_length=400, softening=2.0,
        gravitational_constant=7.4e-26,
        zoom=zoom,
        camera_x=cx - sw / (2 * zoom),
        camera_y=cy - sh / (2 * zoom),
    )
    sun = Planet(
        x=cx, y=cy, radius=40, mass=M_SUN, density=D_SUN,
        fixed_position=True, color=(255, 210, 90),
    )
    gs = gs.with_append_planet(sun)
    G = gs.gravitational_constant
    eps = gs.softening

    # (orbit_r_px = real AU * 150, body_r_px, mass_kg, density_kg_m3, color, moons).
    # moons: list of (r_from_parent_px, body_r_px, mass_kg, density_kg_m3, color, retrograde).
    # Inner planets (Earth, Mars): real Hill spheres are ~1 px at this scale,
    # so moons are not visually possible — only gas giants get moons.
    # Gas-giant moon orbital radii are exaggerated for visibility but well
    # inside each parent's Hill sphere (Jupiter Hill ≈ 53 px, Saturn ≈ 65 px,
    # Uranus ≈ 70 px, Neptune ≈ 116 px). Real masses + densities throughout.
    planets_data = [
        ( 58,  4, M_MERCURY, D_MERCURY, (170, 120,  80), []),   # Mercury 0.39 AU
        (108,  7, M_VENUS,   D_VENUS,   (220, 180, 120), []),   # Venus   0.72
        (150,  8, M_EARTH,   D_EARTH,   (100, 170, 240), []),   # Earth   1.00
        (228,  5, M_MARS,    D_MARS,    (210, 100,  70), []),   # Mars    1.52
        (780,  9, M_JUPITER, D_JUPITER, (220, 180, 130), [      # Jupiter 5.2
            (15, 2, M_IO,       D_IO,       (240, 200, 150), False),
            (22, 2, M_EUROPA,   D_EUROPA,   (220, 220, 180), False),
            (30, 3, M_GANYMEDE, D_GANYMEDE, (190, 180, 160), False),
            (42, 2, M_CALLISTO, D_CALLISTO, (150, 140, 130), False),
        ]),
        (1430, 8, M_SATURN,  D_SATURN,  (230, 200, 140), [      # Saturn 9.54
            (18, 1, M_RHEA,  D_RHEA,  (180, 180, 170), False),
            (32, 3, M_TITAN, D_TITAN, (200, 170, 110), False),
        ]),
        (2880, 6, M_URANUS,  D_URANUS,  (140, 210, 220), [      # Uranus 19.2
            (16, 1, M_TITANIA, D_TITANIA, (170, 170, 170), False),
            (24, 1, M_OBERON,  D_OBERON,  (150, 150, 150), False),
        ]),
        (4515, 6, M_NEPTUNE, D_NEPTUNE, (90,  130, 220), [      # Neptune 30.1
            (28, 2, M_TRITON, D_TRITON, (180, 190, 200), True),
        ]),
    ]

    for r, body_r, mass, density, color, moons in planets_data:
        v = _v_circ_softened(G, eps, M_SUN, r)
        parent = Planet(
            x=cx + r, y=cy, radius=body_r, mass=mass, density=density,
            velocity=(0, v), color=color,
        )
        gs = gs.with_append_planet(parent)
        for i, (m_r, m_body, m_mass, m_density, m_color, retrograde) in enumerate(moons):
            v_m = _v_circ_softened(G, eps, parent.mass, m_r) * (-1.0 if retrograde else 1.0)
            # Spread initial moon phases so they don't all line up radially.
            theta = (i + 1) * (2.0 * math.pi / max(1, len(moons) + 1))
            mx = parent.x + m_r * math.cos(theta)
            my = parent.y + m_r * math.sin(theta)
            mvx = parent.velocity[0] - v_m * math.sin(theta)
            mvy = parent.velocity[1] + v_m * math.cos(theta)
            gs = gs.with_append_planet(Planet(
                x=mx, y=my, radius=m_body, mass=m_mass, density=m_density,
                velocity=(mvx, mvy), color=m_color,
            ))
    return gs


def jupiter_system(state: GameState) -> GameState:
    """Jupiter (fixed) + four Galilean moons with **real masses, real densities,
    and real orbital ratios** (Io 1.0 : Europa 1.59 : Ganymede 2.54 : Callisto 4.47).

    Stable indefinitely because the parent is anchored and there is no
    perturbing third body. Like `solar_system`, `gravitational_constant` is
    tuned to a value that makes Io's orbit visible at our pixel scale.
    """
    gs = _empty(state)
    # Io at r=80 px, T=5 sim-sec target -> v=2π·80/5=100.5 -> G = v²r/M_jup
    gs = gs.copy(
        time_warp=2, trail_length=600, softening=2.0,
        gravitational_constant=4.3e-22,
    )
    cx, cy = 1000, 500
    jupiter = Planet(
        x=cx, y=cy, radius=40, mass=M_JUPITER, density=D_JUPITER,
        fixed_position=True, color=(220, 180, 130),
    )
    gs = gs.with_append_planet(jupiter)
    G = gs.gravitational_constant
    eps = gs.softening

    # (orbit_r_px, body_r_px, mass_kg, density_kg_m3, color)
    # Orbit ratios match real (1 : 1.59 : 2.54 : 4.47); Io scaled to 80 px.
    moons = [
        ( 80, 5, M_IO,       D_IO,       (240, 200, 150)),
        (127, 5, M_EUROPA,   D_EUROPA,   (220, 220, 180)),
        (203, 6, M_GANYMEDE, D_GANYMEDE, (190, 180, 160)),
        (358, 5, M_CALLISTO, D_CALLISTO, (150, 140, 130)),
    ]
    for i, (r, body_r, mass, density, color) in enumerate(moons):
        v = _v_circ_softened(G, eps, M_JUPITER, r)
        # Spread initial phases by 90° so moons don't start radially aligned.
        theta = i * (math.pi / 2)
        gs = gs.with_append_planet(Planet(
            x=cx + r * math.cos(theta), y=cy + r * math.sin(theta),
            radius=body_r, mass=mass, density=density,
            velocity=(-v * math.sin(theta), v * math.cos(theta)),
            color=color,
        ))
    return gs


def binary_star(state: GameState) -> GameState:
    gs = _empty(state)
    cx, cy = 1000, 500
    sep = 220
    body_r, density = 30, 6000
    m = math.pi * body_r * body_r * density
    G = gs.gravitational_constant
    # Two equal stars in mutual circular orbit around shared COM.
    # F = G m^2 / sep^2 = m v^2 / (sep/2)  =>  v = sqrt(G m / (2 sep))
    v = math.sqrt(G * m / (2 * sep))
    gs = gs.with_append_planet(Planet(
        x=cx - sep / 2, y=cy, radius=body_r, density=density,
        velocity=(0, -v), color=(255, 180, 90),
    ))
    gs = gs.with_append_planet(Planet(
        x=cx + sep / 2, y=cy, radius=body_r, density=density,
        velocity=(0, v), color=(110, 160, 255),
    ))
    # Distant lone planet on a wide circular orbit around the COM (treats binary as point mass at d>>sep).
    r = 600
    v_far = _v_circ_softened(G, gs.softening, 2 * m, r)
    gs = gs.with_append_planet(Planet(
        x=cx, y=cy - r, radius=9, density=1200,
        velocity=(v_far, 0), color=(180, 220, 200),
    ))
    return gs


def three_body_lagrange(state: GameState) -> GameState:
    """Three equal masses at the vertices of an equilateral triangle, rotating rigidly."""
    gs = _empty(state)
    cx, cy = 1000, 500
    side = 300
    r_centroid = side / math.sqrt(3)
    body_r, density = 22, 4000
    m = math.pi * body_r * body_r * density
    G = gs.gravitational_constant
    # For an equilateral 3-body in rigid rotation: v = sqrt(G m / side)
    v = math.sqrt(G * m / side)
    colors = [(255, 130, 130), (130, 230, 160), (130, 180, 255)]
    for i in range(3):
        theta = i * 2 * math.pi / 3 + math.pi / 2
        x = cx + r_centroid * math.cos(theta)
        y = cy + r_centroid * math.sin(theta)
        # Tangent velocity: rotate the radial unit vector by +90 degrees.
        vx = -v * math.sin(theta)
        vy = v * math.cos(theta)
        gs = gs.with_append_planet(Planet(
            x=x, y=y, radius=body_r, density=density,
            velocity=(vx, vy), color=colors[i],
        ))
    return gs


def chaotic_swarm(state: GameState) -> GameState:
    gs = _empty(state)
    cx, cy = 1000, 500
    sun = Planet(
        x=cx, y=cy, radius=45, density=10000,
        fixed_position=True, color=(255, 220, 120),
    )
    gs = gs.with_append_planet(sun)
    G = gs.gravitational_constant
    M = sun.mass
    rng = random.Random(42)  # deterministic so screenshots match
    for _ in range(10):
        r = rng.uniform(140, 520)
        theta = rng.uniform(0, 2 * math.pi)
        v_circ = _v_circ_softened(G, gs.softening, M, r)
        # Perturb away from circular: 0.6-1.1 of v_circ -> ellipses, some retrograde via 180-flip random.
        v = v_circ * rng.uniform(0.6, 1.1)
        if rng.random() < 0.15:
            v = -v
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        vx = -v * math.sin(theta)
        vy = v * math.cos(theta)
        gs = gs.with_append_planet(Planet(
            x=x, y=y,
            radius=rng.randint(5, 12),
            density=rng.randint(800, 2000),
            velocity=(vx, vy),
        ))
    return gs


PRESETS: dict[str, tuple[str, callable]] = {
    '1': ('empty', empty),
    '2': ('Sun + Earth', sun_earth),
    '3': ('Solar system', solar_system),
    '4': ('Binary star + planet', binary_star),
    '5': ('Lagrange 3-body', three_body_lagrange),
    '6': ('Chaotic swarm', chaotic_swarm),
    '7': ('Jupiter system', jupiter_system),
}
