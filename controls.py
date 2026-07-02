import math

import pygame

import presets
from collisions import find_first_collision
from objects import GameState, PendingPlanet, Planet


def _remove_planet_under_cursor(state: GameState, screen_xy: tuple[int, int]) -> GameState:
    wx, wy = state.screen_to_world(*screen_xy)
    hit: Planet | None = None
    hit_d = float('inf')
    for p in state.planets:
        d = math.hypot(p.x - wx, p.y - wy)
        if d <= p.radius and d < hit_d:
            hit = p
            hit_d = d
    if hit is None:
        return state
    new_planets = [p for p in state.planets if p is not hit]
    new_tree = GameState.make_kdtree(new_planets) if new_planets else None
    return state.copy(
        planets=new_planets,
        planets_tree=new_tree,
        largest_radius=max((p.radius for p in new_planets), default=0),
    )


def _place_at_center(state: GameState) -> GameState:
    surface = pygame.display.get_surface()
    if surface is None:
        return state
    sw, sh = surface.get_size()
    wx, wy = state.screen_to_world(sw / 2, sh / 2)
    new_planet = Planet(
        x=wx, y=wy,
        radius=state.radius,
        density=state.new_planet_density,
        fixed_position=state.new_planet_fixed_position,
        velocity=(0.0, 0.0),
    )
    if find_first_collision(state, new_planet) is not None:
        return state
    return state.with_append_planet(new_planet)


def handle_interrupts(state: GameState) -> GameState:
    new_state = state

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            new_state = new_state.copy(quit=True)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Use event.pos so the click position is the cursor at event-time, not whenever
            # the poll runs (which can lag by a frame's worth of compute under heavy load).
            mouse_x, mouse_y = event.pos
            world_x, world_y = new_state.screen_to_world(mouse_x, mouse_y)
            pending_planet = PendingPlanet(world_x, world_y, radius=new_state.radius)
            new_state = new_state.copy(pending_planet=pending_planet)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if new_state.pending_planet is not None:
                pending = new_state.pending_planet
                # Recompute final velocity from release-event position so the launch isn't
                # affected by mouse-drift accumulated since the last per-frame preview update.
                rx, ry = event.pos
                pending_sx, pending_sy = new_state.world_to_screen(pending.x, pending.y)
                drag_screen_sq = (rx - pending_sx) ** 2 + (ry - pending_sy) ** 2
                if drag_screen_sq < 9:  # <3 screen px = treat as tap, not drag
                    final_velocity = (0.0, 0.0)
                else:
                    world_rx, world_ry = new_state.screen_to_world(rx, ry)
                    final_velocity = (
                        (pending.x - world_rx) / new_state.velocity_input_scale,
                        (pending.y - world_ry) / new_state.velocity_input_scale,
                    )
                planet = pending.copy(velocity=final_velocity).to_planet()
                if find_first_collision(new_state, planet) is None:
                    new_state = new_state.with_append_planet(planet)
                new_state = new_state.copy(pending_planet=None)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            new_state = new_state.copy(panning=True, pan_last_mouse=pygame.mouse.get_pos())
        if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            new_state = new_state.copy(panning=False, pan_last_mouse=None)
        if event.type == pygame.MOUSEMOTION and new_state.panning and new_state.pan_last_mouse is not None:
            mx, my = event.pos
            lx, ly = new_state.pan_last_mouse
            new_state = new_state.copy(
                camera_x=new_state.camera_x - (mx - lx) / new_state.zoom,
                camera_y=new_state.camera_y - (my - ly) / new_state.zoom,
                pan_last_mouse=(mx, my),
            )
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            world_x, world_y = new_state.screen_to_world(mx, my)
            new_zoom = max(0.05, min(20.0, new_state.zoom * (1.1 ** event.y)))
            new_state = new_state.copy(
                zoom=new_zoom,
                camera_x=world_x - mx / new_zoom,
                camera_y=world_y - my / new_zoom,
            )
        if event.type == pygame.KEYDOWN:
            if pygame.key.name(event.key) == 'k':
                new_state = new_state.copy(radius_change=1)
            elif pygame.key.name(event.key) == 'j':
                new_state = new_state.copy(radius_change=-1)
            elif pygame.key.name(event.key) == 'f':
                new_state = new_state.copy(time_warp_change=1)
            elif pygame.key.name(event.key) == 's':
                new_state = new_state.copy(time_warp_change=-1)
            elif pygame.key.name(event.key) == 'e':
                new_state = new_state.copy(new_planet_density_change=1)
            elif pygame.key.name(event.key) == 'w':
                new_state = new_state.copy(new_planet_density_change=-1)
            elif pygame.key.name(event.key) == ']':
                new_state = new_state.copy(trail_length_change=1)
            elif pygame.key.name(event.key) == '[':
                new_state = new_state.copy(trail_length_change=-1)
        if event.type == pygame.KEYUP:
            if pygame.key.name(event.key) == 'r':
                new_state = GameState()
            elif pygame.key.name(event.key) == 'd':
                new_state = new_state.copy(debug=not new_state.debug)
            elif pygame.key.name(event.key) == 'q':
                new_state = new_state.copy(quit=True)
            elif pygame.key.name(event.key) == 'p':
                new_state = new_state.copy(paused=not new_state.paused)
            elif pygame.key.name(event.key) in ('k', 'j'):
                new_state = new_state.copy(radius_change=0)
            elif pygame.key.name(event.key) in ('f', 's'):
                new_state = new_state.copy(time_warp_change=0)
            elif pygame.key.name(event.key) in ('w', 'e'):
                new_state = new_state.copy(new_planet_density_change=0)
            elif pygame.key.name(event.key) in ('[', ']'):
                new_state = new_state.copy(trail_length_change=0)
            elif pygame.key.name(event.key) == 'g':
                new_state = new_state.copy(new_planet_fixed_position=not new_state.new_planet_fixed_position)
            elif pygame.key.name(event.key) == 'c':
                new_state = _place_at_center(new_state)
            elif pygame.key.name(event.key) == 'x':
                new_state = _remove_planet_under_cursor(new_state, pygame.mouse.get_pos())
            elif pygame.key.name(event.key) in presets.PRESETS:
                _label, fn = presets.PRESETS[pygame.key.name(event.key)]
                new_state = fn(new_state)

    # If we inside the if statement, it means either 'k' or 'j' was being held down.
    # Also, we don't want a negative radius
    new_radius = new_state.radius + new_state.radius_change
    if new_state.radius_change != 0 and new_radius >= 0:
        new_state = new_state.copy(radius=new_radius)

    # If we inside the if statement, it means either 'f' or 's' was being held down.
    # Also, we don't want a negative time warp factor
    new_time_warp = new_state.time_warp + new_state.time_warp_change
    if new_state.time_warp_change != 0 and new_time_warp >= 1:
        new_state = new_state.copy(time_warp=new_time_warp)

    # Trail length: multiplicative steps while '[' / ']' held down. Clamped [50, 200000].
    # Render cost stays bounded because drawing decimates to a fixed point cap.
    if new_state.trail_length_change > 0:
        new_trail = min(200000, int(new_state.trail_length * 1.04) + 1)
        new_state = new_state.copy(trail_length=new_trail)
    elif new_state.trail_length_change < 0:
        new_trail = max(50, int(new_state.trail_length * 0.96))
        new_state = new_state.copy(trail_length=new_trail)

    # Density change: multiplicative steps while 'e' / 'w' held down.
    # ~3x per second at 60 fps, clamped to a sane upper bound so a brief tap
    # doesn't make a 1000x-heavier planet that slingshots everything off-screen.
    if new_state.new_planet_density_change > 0:
        new_density = min(1_000_000, int(new_state.new_planet_density * 1.02) + 1)
        new_state = new_state.copy(new_planet_density=new_density)
    elif new_state.new_planet_density_change < 0:
        new_density = max(1, int(new_state.new_planet_density * 0.98))
        new_state = new_state.copy(new_planet_density=new_density)

    if new_state.pending_planet is not None:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pending_planet = new_state.pending_planet
        pending_sx, pending_sy = new_state.world_to_screen(pending_planet.x, pending_planet.y)
        drag_screen_sq = (mouse_x - pending_sx) ** 2 + (mouse_y - pending_sy) ** 2
        if drag_screen_sq < 9:  # <3 screen px = ignore drift, treat as no drag
            new_velocity = (0.0, 0.0)
        else:
            world_mouse_x, world_mouse_y = new_state.screen_to_world(mouse_x, mouse_y)
            # Slingshot: drag *away* from launch direction. Release sends planet opposite of drag.
            new_velocity = (
                (pending_planet.x - world_mouse_x) / new_state.velocity_input_scale,
                (pending_planet.y - world_mouse_y) / new_state.velocity_input_scale,
            )
        new_pending_planet = pending_planet.copy(
            velocity=new_velocity,
            radius=new_state.radius,
            density=new_state.new_planet_density,
            fixed_position=new_state.new_planet_fixed_position
        )
        new_state = new_state.copy(pending_planet=new_pending_planet)

    return new_state
