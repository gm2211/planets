from objects import Planet, GameState


def any_collisions(candidate: Planet, state: GameState) -> bool:
    if state.planets_tree is None:
        return False

    distance_to_nearest, index_of_nearest = state.planets_tree.query(
        [candidate.x, candidate.y],
        k=1,
        distance_upper_bound=state.largest_radius + candidate.radius + 1
    )

    if index_of_nearest >= len(state.planets):
        return False

    nearest = state.planets[index_of_nearest]

    return distance_to_nearest <= candidate.radius + nearest.radius
