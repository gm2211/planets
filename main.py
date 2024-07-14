import pygame

from controls import handle_interrupts
from drawing import draw
from objects import GameState
from physics import apply_gravitational_forces, move_planets, check_collisions_absorb

if __name__ == '__main__':
    game_state = GameState()

    pygame.init()
    pygame.font.init()
    comic_sans = pygame.font.SysFont('Comic Sans MS', 12)
    display = pygame.display.set_mode(game_state.universe_bottom_right)
    debug = False

    while game_state.running:
        game_state = handle_interrupts(game_state)

        if game_state.pending_planet is None:
            game_state = apply_gravitational_forces(game_state)
            game_state = move_planets(game_state)
            if len(game_state.planets) > 1:
                game_state = check_collisions_absorb(game_state)

        draw(game_state, display, comic_sans, debug)

    pygame.quit()
