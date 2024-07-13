import dataclasses
import time
from typing import List
from dataclasses import dataclass, field

import pygame
from scipy.spatial import KDTree


@dataclass
class Circle:
    x: int = 0
    y: int = 0
    radius: int = 15

    def bounding_box(self) -> pygame.Rect:
        top_left_x = self.x - self.radius
        top_left_y = self.y - self.radius
        return pygame.Rect(top_left_x, top_left_y, self.radius * 2, self.radius * 2)


@dataclass
class PendingCircle:
    x: int
    y: int
    start_time: float

    def to_circle(self) -> Circle:
        size = int(30 * (time.time() - self.start_time))
        return Circle(self.x, self.y, size)


@dataclass
class GameState:
    running: bool = True
    circles: List[Circle] = field(default_factory=list)
    circles_tree: KDTree = None
    pending_circle: PendingCircle = None
    largest_radius: int = 0

    def with_running(self, running: bool) -> 'GameState':
        return dataclasses.replace(self, running=running)

    def with_append_circle(self, circle: Circle) -> 'GameState':
        new_circles = self.circles + [circle]
        return dataclasses.replace(
            self,
            circles=new_circles,
            circles_tree=KDTree([[circle.x, circle.y] for circle in new_circles]),
            largest_radius=max(self.largest_radius, circle.radius)
        )

    def with_pending_circle(self, x: int, y: int) -> 'GameState':
        return dataclasses.replace(self, pending_circle=PendingCircle(x, y, time.time()))
