from functools import singledispatch

from scipy.spatial import KDTree
from typing import List

from objects import Planet, GameState


@singledispatch
def find_first_collision(*args, **kwargs) -> Planet | None:
    raise NotImplementedError("Unsupported type or number of arguments")


@find_first_collision.register
def _(state: GameState, candidate: Planet) -> Planet | None:
    return find_first_collision(candidate, state.planets, state.planets_tree, state.largest_radius)


@find_first_collision.register
def _(
        candidate: Planet,
        planets: List[Planet],
        tree: KDTree,
        largest_radius: float
) -> Planet | None:
    if tree is None:
        return None
    distance_to_nearest, index_of_nearest = tree.query(
        [candidate.x, candidate.y],
        k=1,
        distance_upper_bound=largest_radius + candidate.radius + 1
    )
    if index_of_nearest >= len(planets):
        return None
    nearest = planets[index_of_nearest]
    if distance_to_nearest <= candidate.radius + nearest.radius:
        return nearest
    return None
