# Newtonian Planet Gravity Simulator

A simple, somewhat accurate simulator for gravity between planets.

Somewhat accurate because:
  1. The simulator uses the Newtonian gravity model.
  2. Planets are modeled as circles, not spheres, and we only have 2D space for now.
  3. Integration is **Kick-Drift-Kick leapfrog** — the canonical 2nd-order symplectic integrator for separable Hamiltonians `H = T(p) + V(q)`. Energy oscillates within a bounded envelope but does **not** drift secularly. Plummer softening removes the `1/r²` singularity at close encounter.
  4. Pairwise gravity is computed naively as O(N²), vectorized with numpy. For thousands of bodies you'd want a hierarchical tree (Barnes–Hut) or a higher-order driver like [IAS15 / WHFast in REBOUND](https://rebound.readthedocs.io/). Not needed at this scale.
  5. "Time warp" now means *substeps per render frame* — pure speed control, no longer baked into the force law. Increasing it makes simulated time pass faster without sacrificing integrator accuracy (as long as `dt` stays small).

## Running

```sh
./run.sh
```

That's it. The script will:

1. Install [`uv`](https://github.com/astral-sh/uv) to `~/.local/bin` if it's not already on your `PATH` (no `sudo`, nothing system-wide).
2. Create a project-local `.venv/` and install the pinned dependencies from `pyproject.toml` / `uv.lock`.
3. Launch the simulator.

Requires Python 3.12+. If you don't have one, `uv` will download a managed Python automatically the first time it needs one.

Rendering uses [`pygame-ce`](https://pyga.me/) (community-maintained fork of pygame) for `gfxdraw` antialiased primitives.

## Controls

- `q` quit, `p` pause, `r` reset, `d` toggle debug overlay
- `k` / `j` increase / decrease new planet radius
- `f` / `s` speed up / slow down time warp
- `e` / `w` increase / decrease new planet density
- `[` / `]` shorter / longer trail (capped at 200000 samples ≈ 14 minutes of history at default sampling rate; render is decimated to a fixed segment cap so cost stays bounded)
- `g` toggle "fixed position" for the next planet (a star)
- `c` place a planet at the center of the current view (no drag, zero velocity)
- `x` delete the planet under the cursor
- `1`-`6` load a preset configuration:
  - `1` empty
  - `2` Sun + Earth (one fixed star + one circular orbiter)
  - `3` solar system — sun + 8 planets (Mercury through Neptune) + major moons of the gas giants (Io / Europa / Ganymede / Callisto for Jupiter; Rhea / Titan for Saturn; Titania / Oberon for Uranus; Triton for Neptune). All bodies use **real masses and real densities** (SI: kg, kg/m³). Orbital radii are real AU × 150 px/AU; default zoom is 0.20 so Neptune fits on-screen — wheel-zoom in to inspect the inner system. Moon distances from their parent are exaggerated (real Io is sub-pixel) so they're visible, but kept inside each gas giant's Hill sphere. Inner-planet moons (Luna, Phobos, Deimos) are skipped because Earth's and Mars's real Hill spheres are ~1 px at this scale. `state.gravitational_constant` is calibrated so Earth's orbital period ≈ 30 sim-sec.
  - `7` Jupiter system — fixed Jupiter + the four Galilean moons (Io, Europa, Ganymede, Callisto) with real masses, real densities, and real orbital ratios (1 : 1.59 : 2.54 : 4.47). Stable indefinitely because the parent is anchored and there is no external perturber.
  - `4` binary star + a distant planet
  - `5` Lagrange 3-body (three equal masses at the vertices of an equilateral triangle, rotating rigidly)
  - `6` chaotic swarm (star + 10 perturbed orbits)
  - `7` Jupiter system (fixed Jupiter + Galilean moons — moon demo without a perturbing sun)
- Left-click and drag to place a planet; drag distance sets initial momentum.
- Right-click and drag to pan the camera.
- Mouse wheel to zoom in / out (zoom is anchored at the cursor).
