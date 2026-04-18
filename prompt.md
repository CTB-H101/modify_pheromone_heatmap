You are a senior full-stack + simulation engineer. Build a complete, runnable Python project that simulates pedestrian flow inside Harvard University campus and generates three heatmaps:
1) human flow heatmap
2) congestion heatmap
3) hybrid heatmap

The system must be self-contained (no paid APIs, no keys). Use open data or synthetic data if needed.

========================
[GOAL]
Simulate how students move across campus and visualize where people are and where congestion happens.

========================
[TECH STACK]
- Python 3.11
- networkx (graph modeling)
- numpy (math)
- matplotlib (heatmap)
- optionally: scipy (smoothing)
- no heavy frameworks

========================
[STEP 1: MAP CONSTRUCTION]

Create a simplified graph of Harvard campus using either:
OPTION A (preferred): load from OpenStreetMap using osmnx
OPTION B (fallback): generate a synthetic grid graph (e.g., 50x50 nodes) and label key POIs

Nodes:
- intersections / entrances

Edges:
- walking paths

Each edge must have:
- length (meters)
- capacity (people per minute, estimated)
- free_speed (m/s)

========================
[STEP 2: POINTS OF INTEREST]

Define key nodes:
- dorms (sources)
- classrooms (time-based sinks)
- food trucks / dining halls (main targets)
- libraries

Assign each node:
- attraction weight

========================
[STEP 3: DEMAND GENERATION]

Simulate people over time (e.g., 1 hour, timestep = 1 min)

Use gravity model:
flow_ij = (population_i * attraction_j) / (distance_ij^2 + epsilon)

Add randomness:
- Gaussian noise
- random walkers (10–20%)

Output:
OD pairs with number of people

========================
[STEP 4: PATH SIMULATION]

For each OD pair:
1. Compute initial shortest path (Dijkstra)
2. Then apply slime mold inspired update:

Each edge has conductivity D_ij

Update rule:
dD/dt = |flow| - alpha * D

Simulate multiple iterations:
- distribute flow
- update D
- prune low D edges

Incorporate ant-colony idea:
pheromone = (people_count + speed)

Use pheromone to influence pruning score

========================
[STEP 5: METRICS]

For each edge compute:
- flow (people/min)
- speed (adjusted by congestion)

Speed model:
v = v_free * (1 - flow/capacity)

========================
[STEP 6: HEATMAPS]

Discretize space into grid (e.g., 100x100)

Project edge values onto grid

Generate:

1) Flow heatmap:
value = people density

2) Congestion heatmap:
value = 1 - (v / v_free)

3) Hybrid heatmap:
normalize both then:
score = 0.6 * flow + 0.4 * congestion

Apply Gaussian smoothing

========================
[STEP 7: VISUALIZATION]

Use matplotlib:
- 3 separate plots
- consistent color scale
- titles:
  "Human Flow Heatmap"
  "Congestion Heatmap"
  "Hybrid Heatmap"

Optional:
overlay graph structure

========================
[STEP 8: OUTPUT]

- save images as PNG
- print summary stats:
  - max congestion
  - busiest edge
  - average speed

========================
[CODE REQUIREMENTS]

- clean modular structure:
  main.py
  graph.py
  simulation.py
  visualization.py

- include comments explaining logic
- include a "run_all()" entry point

========================
[EXTRA]

If osmnx fails:
automatically fallback to synthetic grid

========================
[IMPORTANT]

Do NOT skip simulation logic.
Do NOT hardcode fake heatmaps.
Everything must be computed.

Return full code.