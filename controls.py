import pygame

from collisions import find_first_collision
from objects import GameState, PendingPlanet


def handle_interrupts(state: GameState) -> GameState:
    new_state = state

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            new_state = new_state.copy(quit=True)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            new_state = new_state.copy(pending_planet=PendingPlanet(mouse_x, mouse_y, radius=new_state.radius))
        if event.type == pygame.MOUSEBUTTONUP:
            if new_state.pending_planet is not None:
                planet = new_state.pending_planet.to_planet()
                if find_first_collision(new_state, planet) is None:
                    new_state = new_state.with_append_planet(planet)
                new_state.pending_planet = None
        if event.type == pygame.KEYDOWN:
            if pygame.key.name(event.key) == 'k':
                new_state = new_state.copy(radius_change=1)
            elif pygame.key.name(event.key) == 'j':
                new_state = new_state.copy(radius_change=-1)
        if event.type == pygame.KEYUP:
            if pygame.key.name(event.key) == 'r':
                new_state = GameState()
            elif pygame.key.name(event.key) == 'q':
                new_state = new_state.copy(quit=True)
            elif pygame.key.name(event.key) == 'p':
                paused = not new_state.paused
                new_state = new_state.copy(paused=paused)
            elif pygame.key.name(event.key) in ('k', 'j'):
                new_state = new_state.copy(radius_change=0)

    if new_state.radius_change != 0:
        new_state = new_state.copy(radius=new_state.radius + new_state.radius_change)

    if new_state.pending_planet is not None:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pending_planet = new_state.pending_planet
        new_momentum = (
            -(pending_planet.x - mouse_x) / GameState.momentum_vector_scale_factor,
            -(pending_planet.y - mouse_y) / GameState.momentum_vector_scale_factor
        )
        new_pending_planet = pending_planet.copy(momentum=new_momentum, radius=new_state.radius)
        new_state = new_state.copy(pending_planet=new_pending_planet)

    return new_state
