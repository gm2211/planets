import pygame

from controls import handle_interrupts
from drawing import draw, write_text
from objects import GameState
from physics import apply_gravitational_forces, move_planets, check_collisions_absorb

if __name__ == '__main__':
    game_state = GameState()

    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode(game_state.universe_bottom_right)

    while not game_state.quit:
        game_state = handle_interrupts(game_state)

        if game_state.paused:
            write_text(
                GameState.universe_bottom_right[0] / 2,
                GameState.universe_bottom_right[1] / 2,
                'PAUSED',
                display
            )
            pygame.display.flip()
            continue

        if game_state.pending_planet is None:
            game_state = apply_gravitational_forces(game_state)
            game_state = move_planets(game_state)
            if len(game_state.planets) > 1:
                game_state = check_collisions_absorb(game_state)

        draw(game_state, display)

    pygame.quit()
