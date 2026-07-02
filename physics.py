"""Hamiltonian (symplectic) integrator for an N-body planet system.

Uses Kick-Drift-Kick (KDK) leapfrog, the canonical 2nd-order symplectic
integrator for separable Hamiltonians of the form

    H(q, p) = sum_i  p_i^2 / (2 m_i)   +   - sum_{i<j} G m_i m_j / r_ij

Energy oscillates within a bounded envelope but does not drift secularly
(unlike forward Euler, which the prior implementation effectively was).

Plummer softening epsilon avoids the 1/r^2 singularity at close encounter:

    a_i = G * sum_{j != i}  m_j * (r_j - r_i) / (|r_j - r_i|^2 + eps^2)^(3/2)
"""

import math

import numpy as np

from collisions import find_first_collision
from objects import GameState


def _compute_accelerations(
        positions: np.ndarray,  # (N, 2)
        masses: np.ndarray,     # (N,)
        fixed: np.ndarray,      # (N,) bool
        G: float,
        soft2: float,
) -> np.ndarray:
    n = positions.shape[0]
    if n < 2:
        return np.zeros_like(positions)

    # diff[i, j] = positions[j] - positions[i]  (vector pointing from i toward j)
    diff = positions[np.newaxis, :, :] - positions[:, np.newaxis, :]  # (N, N, 2)
    d2 = (diff * diff).sum(axis=2) + soft2  # (N, N)
    inv_d3 = d2 ** -1.5
    np.fill_diagonal(inv_d3, 0.0)  # no self-interaction

    # a_i = G * sum_j m_j * diff_ij / d_ij^3
    accel = G * (masses[np.newaxis, :, np.newaxis] * diff * inv_d3[:, :, np.newaxis]).sum(axis=1)

    accel[fixed] = 0.0
    return accel


def step(state: GameState) -> GameState:
    """Advance the simulation by `state.time_warp` KDK substeps of `state.dt` each.

    Collision detection runs after every substep so close encounters that swing
    through periapsis within a single frame still merge — otherwise the pair
    appears to bounce as they cross and then get pulled back together next frame.
    """
    substeps = max(1, state.time_warp)
    half_dt = 0.5 * state.dt
    G = state.gravitational_constant
    soft2 = state.softening ** 2
    dt = state.dt

    for _ in range(substeps):
        planets = state.planets
        n = len(planets)
        if n == 0:
            break

        positions = np.array([[p.x, p.y] for p in planets], dtype=np.float64)
        velocities = np.array([p.velocity for p in planets], dtype=np.float64)
        masses = np.array([p.mass for p in planets], dtype=np.float64)
        fixed = np.array([p.fixed_position for p in planets], dtype=bool)
        moving = ~fixed

        # KDK leapfrog substep.
        accel = _compute_accelerations(positions, masses, fixed, G, soft2)
        velocities[moving] += half_dt * accel[moving]
        positions[moving] += dt * velocities[moving]
        accel = _compute_accelerations(positions, masses, fixed, G, soft2)
        velocities[moving] += half_dt * accel[moving]

        # Commit state back to planet objects (mutated in place; refs stable).
        cap = state.trail_length
        for i, p in enumerate(planets):
            p.x = float(positions[i, 0])
            p.y = float(positions[i, 1])
            p.velocity = (float(velocities[i, 0]), float(velocities[i, 1]))
            p.max_track_length = cap  # sync cap so '[' / ']' resizes live
            p.track.append((p.x, p.y))
            while len(p.track) > cap:
                p.track.popleft()

        # Catch collisions that opened and closed within this frame.
        if len(planets) > 1:
            state = check_collisions_absorb(state)

    if not state.planets:
        return state.copy(planets_tree=None)
    return state.copy(planets_tree=GameState.make_kdtree(state.planets))


def check_collisions_absorb(state: GameState) -> GameState:
    """Merge colliding planets, conserving total momentum and mass."""
    if len(state.planets) < 2:
        return state

    new_state = state.with_no_planets()
    planets = list(state.planets)
    removed = set()

    for planet in planets:
        if id(planet) in removed:
            continue

        candidates = [p for p in planets if id(p) not in removed and p is not planet]
        if not candidates:
            new_state = new_state.with_append_planet(planet)
            continue

        collision = find_first_collision(
            planet,
            candidates,
            GameState.make_kdtree(candidates),
            max(c.radius for c in candidates),
        )

        if collision is None:
            new_state = new_state.with_append_planet(planet)
            continue

        survivor, dying = (
            (planet, collision)
            if planet.mass > collision.mass
            else (collision, planet)
        )

        m_s, m_d = survivor.mass, dying.mass
        total_mass = m_s + m_d
        # Cube-root scaling for the visible radius — physically motivated by
        # constant-density 3D volume addition (V ~ r^3, so r ~ M^(1/3)).
        new_radius = survivor.radius * (total_mass / m_s) ** (1.0 / 3.0)
        # Mass-weighted density (so the merged body's stored density is the
        # right average — matters if the user later inspects it or merges again).
        new_density = (m_s * survivor.density + m_d * dying.density) / total_mass

        if survivor.fixed_position:
            new_velocity = (0.0, 0.0)
        else:
            # Conservation of linear momentum: M*V = m_s*v_s + m_d*v_d
            new_velocity = (
                (m_s * survivor.velocity[0] + m_d * dying.velocity[0]) / total_mass,
                (m_s * survivor.velocity[1] + m_d * dying.velocity[1]) / total_mass,
            )

        merged = survivor.copy(
            radius=new_radius,
            velocity=new_velocity,
            mass=total_mass,
            density=new_density,
        )
        new_state = new_state.with_append_planet(merged)
        removed.add(id(dying))
        # Survivor's old identity is also gone (replaced by `merged`); keep it out of future iters.
        removed.add(id(survivor))

    return new_state
