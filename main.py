import pygame

from collisions import any_collisions
from objects import GameState


def handle_interrupts(state: GameState) -> GameState:
    new_state = state

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            new_state = new_state.with_running(False)
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            new_state = new_state.with_pending_circle(x, y)
        if event.type == pygame.MOUSEBUTTONUP:
            if new_state.pending_circle is not None:
                circle = new_state.pending_circle.to_circle()
                if not any_collisions(circle, new_state):
                    new_state = new_state.with_append_circle(circle)
                new_state.pending_circle = None

    return new_state


def draw(state: GameState, screen: pygame.Surface):
    screen.fill((0, 0, 0))

    for circle in state.circles:
        pygame.draw.circle(screen, white, (circle.x, circle.y), circle.radius)

    if state.pending_circle is not None:
        pending_circle = state.pending_circle.to_circle()

        pygame.draw.circle(
            screen,
            white,
            (pending_circle.x, pending_circle.y),
            pending_circle.radius
        )

    pygame.display.flip()


if __name__ == '__main__':
    white = (255, 255, 255)

    pygame.init()
    display = pygame.display.set_mode([500, 500])
    game_state = GameState()

    while game_state.running:
        game_state = handle_interrupts(game_state)
        draw(game_state, display)

    pygame.quit()
