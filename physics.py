import math

import scipy.constants

from collisions import find_first_collision
from objects import GameState


# How much a body is accelerated towards the body with mass 'm' at distance d
def gravity_acceleration(m: float, d: float) -> float:
    # F = G * m1 * m2 / d^2,
    # a = F / m1,
    # a = G * m2 / d^2
    return scipy.constants.G * m / max(scipy.constants.epsilon_0, d ** 2)


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
    new_state = state.copy().clear_planets()

    for planet in state.planets:
        moved_planet = planet.copy()
        moved_planet.save_cur_pos_to_track()

        moved_planet.x -= planet.momentum[0] * 5
        moved_planet.y -= planet.momentum[1] * 5

        new_state = new_state.with_append_planet(moved_planet)

    return new_state


def check_collisions_absorb(state: GameState) -> GameState:
    new_state = state.copy().clear_planets()
    planets = state.planets.copy()
    removed_planets = []

    for planet in planets:
        if planet in removed_planets:
            continue

        planets_to_consider = list(set(planets) - set(removed_planets) - {planet})

        if len(planets_to_consider) == 0:
            new_state = new_state.with_append_planet(planet)
            continue

        collision = find_first_collision(
            planet,
            planets_to_consider,
            GameState.make_kdtree(planets_to_consider),
            max(planets_to_consider, key=lambda p: p.radius).radius
        )

        if collision is None:
            new_state = new_state.with_append_planet(planet)
            continue

        surviving_planet, dying_planet = (
            (planet, collision)
            if planet.mass() > collision.mass()
            else (collision, planet)
        )
        dying_planet_mass_ratio = dying_planet.mass() / (surviving_planet.mass() + dying_planet.mass())
        new_mass = surviving_planet.mass() + dying_planet.mass()
        new_radius = math.sqrt(new_mass / surviving_planet.density / math.pi)
        surviving_with_absorbed = surviving_planet.copy(
            radius=new_radius,
            momentum=(
                surviving_planet.momentum[0] + (dying_planet.momentum[0] * dying_planet_mass_ratio),
                surviving_planet.momentum[1] + (dying_planet.momentum[1] * dying_planet_mass_ratio)
            )
        )
        new_state = new_state.with_append_planet(surviving_with_absorbed)
        removed_planets.append(dying_planet)

    return new_state
