import dataclasses
import math
import time
from typing import List
from dataclasses import dataclass, field

import pygame
from scipy.spatial import KDTree


@dataclass
class Planet:
    x: float = 0
    y: float = 0
    radius: int = 15
    momentum: (float, float) = (0, 0)
    density: int = 100

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


@dataclass
class PendingPlanet:
    x: int
    y: int
    start_time: float

    def to_planet(self) -> Planet:
        size = int(30 * (time.time() - self.start_time))
        return Planet(self.x, self.y, size)


@dataclass
class GameState:
    running: bool = True
    planets: List[Planet] = field(default_factory=list)
    planets_tree: KDTree = None
    pending_planet: PendingPlanet = None
    largest_radius: int = 0
    universe_bottom_right = (1000, 1000)

    def copy(self, **changes) -> 'GameState':
        return dataclasses.replace(self, **changes)

    def with_running(self, running: bool) -> 'GameState':
        return self.copy(running=running)

    def with_append_planet(self, planet: Planet) -> 'GameState':
        new_planets = self.planets + [planet]
        return self.copy(
            planets=new_planets,
            planets_tree=KDTree([[planet.x, planet.y] for planet in new_planets]),
            largest_radius=max(self.largest_radius, planet.radius)
        )

    def with_pending_planet(self, x: int, y: int) -> 'GameState':
        return self.copy(pending_planet=PendingPlanet(x, y, time.time()))
