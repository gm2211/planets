import colorsys
import dataclasses
import math
import random
from collections import deque
from dataclasses import dataclass, field

import pygame
from scipy.spatial import KDTree

type Point = tuple[float, float]
type Color = tuple[int, int, int]


def _random_planet_color() -> Color:
    h = random.random()
    s = 0.55 + random.random() * 0.35
    v = 0.85 + random.random() * 0.15
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


@dataclass
class Planet:
    x: float = 0
    y: float = 0
    radius: float = 15
    velocity: Point = (0, 0)  # world units per second
    density: float = 1_000  # real density (kg/m^3 for preset bodies; arbitrary for UI-placed)
    mass: float = 0.0  # if 0 at construction, derived from area() * density
    fixed_position: bool = False
    track: deque[Point] = field(default_factory=deque)
    max_track_length: int = 600
    color: Color = field(default_factory=_random_planet_color)

    def __post_init__(self):
        # Allow callers to either supply mass directly (presets w/ real values)
        # or let it be derived from radius+density (UI-placed planets).
        if self.mass == 0:
            self.mass = math.pi * self.radius ** 2 * self.density

    def copy(self, **changes) -> 'Planet':
        return dataclasses.replace(self, **changes)

    def bounding_box(self) -> pygame.Rect:
        top_left_x = self.x - self.radius
        top_left_y = self.y - self.radius
        return pygame.Rect(top_left_x, top_left_y, self.radius * 2, self.radius * 2)

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def distance_to(self, planet: 'Planet') -> float:
        return math.sqrt((self.x - planet.x) ** 2 + (self.y - planet.y) ** 2)

    def save_cur_pos_to_track(self):
        self.track.append((self.x, self.y))
        while len(self.track) > self.max_track_length:
            self.track.popleft()

    def __hash__(self):
        return hash((
            self.x,
            self.y,
            self.radius,
            self.velocity[0],
            self.velocity[1],
            self.density,
        ))


@dataclass
class PendingPlanet:
    x: float
    y: float
    radius: int = 15
    density: int = 1_000
    velocity: Point = (0, 0)
    fixed_position: bool = False
    color: Color = field(default_factory=_random_planet_color)

    def copy(self, **changes) -> 'PendingPlanet':
        return dataclasses.replace(self, **changes)

    def to_planet(self) -> Planet:
        velocity = self.velocity if not self.fixed_position else (0, 0)
        return Planet(
            x=self.x,
            y=self.y,
            radius=self.radius,
            velocity=velocity,
            density=self.density,
            fixed_position=self.fixed_position,
            color=self.color,
        )


@dataclass(frozen=True)
class GameState:
    quit: bool = False
    paused: bool = False
    debug: bool = False
    radius: int = 15
    radius_change: int = 0
    # Substeps per render frame. Bigger = faster apparent time. Pure speed knob, not in force law.
    time_warp: int = 5
    time_warp_change: int = 0
    new_planet_density: int = 1_000
    new_planet_density_change: int = 0
    planets: list[Planet] = field(default_factory=list)
    planets_tree: KDTree | None = None
    pending_planet: PendingPlanet | None = None
    largest_radius: float = 0
    universe_bottom_right: tuple[int, int] = (2000, 1000)
    velocity_input_scale: float = 15.0
    new_planet_fixed_position: bool = False
    camera_x: float = 0.0
    camera_y: float = 0.0
    zoom: float = 1.0
    panning: bool = False
    pan_last_mouse: tuple[int, int] | None = None
    # Trail length (per-planet sample cap). Synced onto every Planet each frame.
    trail_length: int = 2000
    trail_length_change: int = 0
    # Hamiltonian integrator parameters.
    dt: float = 0.02  # integration timestep, "seconds"
    gravitational_constant: float = 0.03  # effective G chosen for visible dynamics at default scales
    softening: float = 15.0  # Plummer softening (~ default planet radius); avoids 1/r^2 singularity

    @staticmethod
    def make_kdtree(planets: list[Planet]) -> KDTree:
        return KDTree([[planet.x, planet.y] for planet in planets])

    def world_to_screen(self, wx: float, wy: float) -> tuple[float, float]:
        return (wx - self.camera_x) * self.zoom, (wy - self.camera_y) * self.zoom

    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        return sx / self.zoom + self.camera_x, sy / self.zoom + self.camera_y

    def copy(self, **changes) -> 'GameState':
        return dataclasses.replace(self, **changes)

    def with_append_planet(self, planet: Planet) -> 'GameState':
        new_planets = self.planets + [planet]
        return self.copy(
            planets=new_planets,
            planets_tree=self.make_kdtree(new_planets),
            largest_radius=max(self.largest_radius, planet.radius)
        )

    def with_no_planets(self) -> 'GameState':
        return self.copy(planets=[], planets_tree=None, largest_radius=0)
