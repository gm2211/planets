import pygame

from objects import Planet, GameState

white = (255, 255, 255)
yellow = (255, 255, 0)


def draw(state: GameState, screen: pygame.Surface, debug: bool):
    screen.fill((0, 0, 0))
    write_text(
        0, 0,
        'Press "q" to quit, "p" to pause, "r" to reset, "k" to increase radius, "j" to decrease radius',
        screen
    )
    write_text(0, 20, f'radius: {state.radius}', screen)
    write_text(0, 70, f'time warp: {state.time_warp}', screen)
    border = 1 if debug else 0

    for planet in state.planets:
        draw_planet(state, planet, border, screen)
        if debug:
            describe_planet(planet, screen)

    if state.pending_planet is not None:
        pending_planet = state.pending_planet.to_planet()
        draw_planet(state, pending_planet, border, screen)

    pygame.display.flip()


def draw_planet(state: GameState, planet: Planet, border: int, screen: pygame.Surface):
    global white
    pygame.draw.circle(screen, white, (planet.x, planet.y), planet.radius, width=border)

    # Draw the momentum vector
    pygame.draw.line(
        screen,
        white,
        (planet.x, planet.y),
        # Multiply by 100 to make the vector more visible
        (
            planet.x - planet.momentum[0] * state.momentum_input_scale,
            planet.y - planet.momentum[1] * state.momentum_input_scale
        ),
    )
    for x, y in planet.track:
        pygame.draw.circle(screen, yellow, (x, y), 1)


def describe_planet(planet: Planet, screen: pygame.Surface):
    text: str = f'PLANET' \
                f'coord: ({planet.x}, {planet.y}),' \
                f'mass: {planet.mass():.2f},' \
                f'traj: ({planet.momentum[0]}, {planet.momentum[1]})'
    write_text(planet.x, planet.y, text, screen)


def write_text(x: float, y: float, text: str, screen: pygame.Surface):
    global white
    comic_sans = pygame.font.SysFont('Comic Sans MS', 12)
    screen.blit(
        source=comic_sans.render(text, False, white),
        dest=(x, y)
    )
