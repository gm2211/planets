import time

import pygame

from collisions import any_collisions
from objects import GameState, Planet
from physics import apply_gravitational_forces, move_planets


def handle_interrupts(state: GameState) -> GameState:
    new_state = state

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            new_state = new_state.with_running(False)
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            new_state = new_state.with_pending_planet(x, y)
        if event.type == pygame.MOUSEBUTTONUP:
            if new_state.pending_planet is not None:
                planet = new_state.pending_planet.to_planet()
                if not any_collisions(planet, new_state):
                    new_state = new_state.with_append_planet(planet)
                new_state.pending_planet = None
        if event.type == pygame.KEYUP and pygame.key.name(event.key) == 'r':
            new_state = GameState()

    return new_state


def draw(state: GameState, screen: pygame.Surface, font: pygame.font.Font, debug: bool):
    screen.fill((0, 0, 0))
    border = 1 if debug else 0

    for planet in state.planets:
        pygame.draw.circle(screen, white, (planet.x, planet.y), planet.radius, width=border)
        pygame.draw.line(
            screen,
            white,
            (planet.x, planet.y),
            (planet.x - planet.momentum[0], planet.y - planet.momentum[1])
        )
        if debug:
            describe_planet(planet, font, screen)

    if state.pending_planet is not None:
        pending_planet = state.pending_planet.to_planet()

        pygame.draw.circle(
            screen,
            white,
            (pending_planet.x, pending_planet.y),
            pending_planet.radius,
            width=border
        )

    pygame.display.flip()


def describe_planet(planet: Planet, the_font: pygame.font.Font, screen: pygame.Surface):
    screen.blit(
        source=the_font.render(
            f'PLANET'
            f'coord: ({planet.x}, {planet.y}),'
            f'mass: {planet.mass():.2f},'
            f'traj: ({planet.momentum[0] + planet.x}, {planet.momentum[1] + planet.y})',
            False,
            white
        ),
        dest=(planet.x, planet.y))


if __name__ == '__main__':
    white = (255, 255, 255)
    game_state = GameState()

    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont('Comic Sans MS', 12)
    display = pygame.display.set_mode(game_state.universe_bottom_right)
    debug = True

    while game_state.running:
        game_state = handle_interrupts(game_state)

        if game_state.pending_planet is None:
            game_state = apply_gravitational_forces(game_state)
            game_state = move_planets(game_state)

        draw(game_state, display, font, debug)

    pygame.quit()
