import scipy.constants

from objects import GameState


# How much a body is accelerated towards the body with mass 'm' at distance d
def gravity_acceleration(m: float, d: float) -> float:
    # F = G * m1 * m2 / d^2,
    # a = F / m1,
    # a = G * m2 / d^2
    return scipy.constants.G * m / d ** 2


def apply_gravitational_forces(state: GameState) -> GameState:
    if len(state.planets) < 2:
        return state

    new_state = state.copy()

    for target_planet in new_state.planets:
        forces = [target_planet.momentum]

        for attracting_planet in new_state.planets:
            if attracting_planet == target_planet:
                continue
            gravity_magnitude = gravity_acceleration(
                attracting_planet.mass(),
                target_planet.distance_to(attracting_planet)
            )
            forces.append(
                (
                    gravity_magnitude * (target_planet.x - attracting_planet.x),
                    gravity_magnitude * (target_planet.y - attracting_planet.y)
                )
            )

        total_force = (
            sum([force[0] for force in forces]),
            sum([force[1] for force in forces])
        )

        target_planet.momentum = total_force

    return new_state


def move_planets(state: GameState) -> GameState:
    new_state = state.copy()

    new_state.planets = []
    new_state.planets_tree = None
    new_state.largest_radius = 0

    for planet in state.planets:
        moved_planet = planet.copy()

        moved_planet.x -= planet.momentum[0]
        moved_planet.y -= planet.momentum[1]

        new_state = new_state.with_append_planet(moved_planet)

    return new_state
