from objects import Circle, GameState


def any_collisions(candidate: Circle, state: GameState) -> bool:
    if state.circles_tree is None:
        return False

    distance_to_nearest, index_of_nearest = state.circles_tree.query(
        [candidate.x, candidate.y],
        k=1,
        distance_upper_bound=state.largest_radius + candidate.radius + 1
    )

    if index_of_nearest >= len(state.circles):
        return False

    nearest = state.circles[index_of_nearest]

    return distance_to_nearest <= candidate.radius + nearest.radius
