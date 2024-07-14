import pygame

from collisions import find_first_collision
from objects import GameState


def handle_interrupts(state: GameState) -> GameState:
    new_state = state

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            new_state = new_state.with_running(False)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            new_state = new_state.with_pending_planet(mouse_x, mouse_y)
        if event.type == pygame.MOUSEBUTTONUP:
            if new_state.pending_planet is not None:
                planet = new_state.pending_planet.to_planet()
                if find_first_collision(new_state, planet) is None:
                    new_state = new_state.with_append_planet(planet)
                new_state.pending_planet = None
        if event.type == pygame.KEYUP:
            if pygame.key.name(event.key) == 'r':
                new_state = GameState()
            elif pygame.key.name(event.key) == 'q':
                new_state = new_state.with_running(False)

    if new_state.pending_planet is not None:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        scale_factor = 10_000
        pending_planet = new_state.pending_planet
        new_momentum = (
            -(pending_planet.x - mouse_x) / scale_factor,
            -(pending_planet.y - mouse_y) / scale_factor
        )
        print(new_momentum)
        new_pending_planet = pending_planet.copy(momentum=new_momentum)
        new_state = new_state.copy(pending_planet=new_pending_planet)

    return new_state
