import time
from typing import List
from dataclasses import dataclass, field

import pygame


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
        size = int(100 * (time.time() - self.start_time))
        return Circle(self.x, self.y, size)


@dataclass
class GameState:
    running: bool = True
    circles: List[Circle] = field(default_factory=list)
    pending_circle: PendingCircle = None

    def with_running(self, running: bool) -> 'GameState':
        return GameState(running=running, circles=self.circles)

    def with_append_circle(self, circle: Circle) -> 'GameState':
        return GameState(running=self.running, circles=self.circles + [circle])

    def with_pending_circle(self, x: int, y: int) -> 'GameState':
        return GameState(
            running=self.running,
            circles=self.circles,
            pending_circle=PendingCircle(x, y, time.time())
        )
