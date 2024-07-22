# Newtonian Planet Gravity Simulator

A simple, somewhat accurate simulator for gravity between planets.

Somewhat accurate because:
  1. The simulator uses the newtonian gravity model
  2. Planets are modeled as circles, not spheres and we only have 2d space for now
  1. Gravity is naively computed between planets, pair-wise and does not use hamiltonians (https://academic.oup.com/mnras/article/440/1/719/1747624)
  1. There's a concept of "time warp", which is meant to allow you to speed up the simulation - it uses made up multiplications that seem to work, but are not really based in physics - the physics should be more or less accurate if time_warp = 1.
