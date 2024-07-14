import dataclasses
import math
from dataclasses import dataclass, field
from typing import List

import pygame
from scipy.spatial import KDTree


@dataclass
class Planet:
    x: float = 0
    y: float = 0
    radius: int = 15
    momentum: (float, float) = (0, 0)
    density: int = 1_000

    def copy(self, **changes) -> 'Planet':
        return dataclasses.replace(self, **changes)

    def bounding_box(self) -> pygame.Rect:
        top_left_x = self.x - self.radius
        top_left_y = self.y - self.radius
        return pygame.Rect(top_left_x, top_left_y, self.radius * 2, self.radius * 2)

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def mass(self) -> float:
        return self.area() * self.density

    def distance_to(self, planet: 'Planet') -> float:
        return math.sqrt((self.x - planet.x) ** 2 + (self.y - planet.y) ** 2)

    def __hash__(self):
        return hash((self.x, self.y, self.radius, self.momentum[0], self.momentum[1], self.density))


@dataclass
class PendingPlanet:
    x: int
    y: int
    radius: int = 15
    momentum: (float, float) = (0, 0)

    def copy(self, **changes) -> 'PendingPlanet':
        return dataclasses.replace(self, **changes)

    def to_planet(self) -> Planet:
        return Planet(self.x, self.y, radius=self.radius, momentum=self.momentum)


@dataclass
class GameState:
    quit: bool = False
    paused: bool = False
    radius: int = 15
    radius_change: int = 0  # -1 for decreasing, 0 for now change, 1 for increasing
    planets: List[Planet] = field(default_factory=list)
    planets_tree: KDTree | None = None
    pending_planet: PendingPlanet | None = None
    largest_radius: float = 0
    universe_bottom_right = (2000, 1000)
    momentum_vector_scale_factor = 5_000

    @staticmethod
    def make_kdtree(planets: List[Planet]) -> KDTree:
        return KDTree([[planet.x, planet.y] for planet in planets])

    def copy(self, **changes) -> 'GameState':
        return dataclasses.replace(self, **changes)

    def with_append_planet(self, planet: Planet) -> 'GameState':
        new_planets = self.planets + [planet]
        return self.copy(
            planets=new_planets,
            planets_tree=self.make_kdtree(new_planets),
            largest_radius=max(self.largest_radius, planet.radius)
        )

    def clear_planets(self) -> 'GameState':
        self.planets = []
        self.planets_tree = None
        self.largest_radius = 0
        return self
