# simulation.py
"""
Pedestrian flow simulation, gravity model, slime mold/ant-colony update, and metrics.
"""
import numpy as np
import networkx as nx
from collections import defaultdict
from tqdm import trange, tqdm
import itertools


def run_simulation(
    G,
    pois,
    duration=60,
    timestep=1,
    alpha=0.1,
    epsilon=1e-3,
    sim_iters=10,
    grid_size=100,
    gaussian_sigma=2,
    random_walker_frac=0.15,
    random_walker_min=5,
    random_walker_max=20,
    population_min=30,
    population_max=80,
    flow_noise_frac=0.1,
    path_mode="shortest",
    k_shortest=3,
    random_seed=None,
):
    """
    Simulate pedestrian flow and compute edge/grid metrics.
    Returns:
        edge_metrics: dict
        grid_metrics: dict
        summary: dict
    """
    # Set RNG for reproducibility if requested
    if random_seed is not None:
        np.random.seed(random_seed)

    # Step 3: Demand generation (gravity model)
    # 基础 OD: 允许任意已标注的 POI 作为源或汇
    sources = list(pois.keys())
    sinks = list(pois.keys())
    population = {n: np.random.randint(population_min, population_max) for n in sources}
    attraction = {n: pois[n]["weight"] for n in sinks}
    # Precompute shortest path lengths
    lengths = dict(nx.all_pairs_dijkstra_path_length(G, weight="length"))
    od_flows = defaultdict(float)
    for i in tqdm(sources, desc="Gravity Model (sources)", unit="src"):
        for j in sinks:
            if i == j or j not in lengths[i]:
                continue
            dist = lengths[i][j]
            flow = (population[i] * attraction[j]) / (dist ** 2 + epsilon)
            flow += np.random.normal(0, flow_noise_frac * flow)  # Gaussian noise
            if flow > 0:
                od_flows[(i, j)] += max(flow, 0)
    # Add random walkers
    all_nodes = list(G.nodes)
    n_random = int(random_walker_frac * max(1, len(od_flows)))
    for _ in tqdm(range(n_random), desc="Random Walkers", unit="rw"):
        i, j = np.random.choice(all_nodes, 2, replace=False)
        od_flows[(i, j)] += np.random.uniform(random_walker_min, random_walker_max)
    # Step 4: Path simulation (slime mold + ant-colony)
    # 为兼容 MultiDiGraph，使用带 key 的 edge tuple (u,v,k) 作为字典键
    if G.is_multigraph():
        D = {(u, v, k): 1.0 for u, v, k in G.edges(keys=True)}
        pheromone = {(u, v, k): 0.0 for u, v, k in G.edges(keys=True)}
    else:
        D = {(u, v): 1.0 for u, v in G.edges}
        pheromone = {(u, v): 0.0 for u, v in G.edges
                     }
    for t in trange(sim_iters, desc="Path Simulation", unit="iter"):
        edge_flow = defaultdict(float)
        for (i, j), f in tqdm(od_flows.items(), desc="OD Shortest Paths", unit="OD", leave=False):
            try:
                def weight_func(u, v, d):
                    # 获取与边对应的 D 值，兼容 multi/uni graph
                    if G.is_multigraph():
                        # 如果 (u,v,k) 存在则取第一个 key
                        try:
                            k = next(iter(G[u][v]))
                            dval = D.get((u, v, k), 1.0)
                        except Exception:
                            dval = 1.0
                    else:
                        dval = D.get((u, v), D.get((v, u), 1.0))
                    if "length" not in d or dval is None:
                        return 1e9  # 极大权重，跳过无效边
                    return d["length"] / (dval + 1e-2)

                # 支持多种路径策略
                if path_mode == "shortest":
                    path = nx.shortest_path(G, i, j, weight=weight_func)
                elif path_mode == "stochastic_k":
                    try:
                        paths_gen = nx.shortest_simple_paths(G, i, j, weight=weight_func)
                        candidates = list(itertools.islice(paths_gen, k_shortest))
                        if not candidates:
                            continue

                        def path_cost(p):
                            cost = 0.0
                            for u, v in zip(p[:-1], p[1:]):
                                if G.is_multigraph():
                                    try:
                                        k0 = next(iter(G[u][v]))
                                        d0 = G[u][v][k0]
                                    except Exception:
                                        d0 = list(G[u][v].values())[0]
                                else:
                                    d0 = G[u][v]
                                cost += weight_func(u, v, d0)
                            return cost

                        costs = np.array([path_cost(p) for p in candidates])
                        probs = (1.0 / (costs + 1e-6))
                        probs = probs / probs.sum()
                        idx = np.random.choice(len(candidates), p=probs)
                        path = candidates[int(idx)]
                    except Exception:
                        continue
                elif path_mode == "random_walk":
                    current = i
                    path = [i]
                    max_steps = max(50, len(G) * 4)
                    steps = 0
                    while current != j and steps < max_steps:
                        # neighbors for MultiGraph vs Graph
                        if G.is_multigraph():
                            neighs = list(G[current].keys())
                        else:
                            neighs = list(G[current])
                        if not neighs:
                            break
                        weights = []
                        for nb in neighs:
                            if G.is_multigraph():
                                try:
                                    k0 = next(iter(G[current][nb]))
                                    d0 = G[current][nb][k0]
                                except Exception:
                                    d0 = list(G[current][nb].values())[0]
                            else:
                                d0 = G[current][nb]
                            weights.append(1.0 / (d0.get("length", 1.0) + 1e-6))
                        probs = np.array(weights) / np.sum(weights)
                        nb = np.random.choice(neighs, p=probs)
                        path.append(nb)
                        current = nb
                        steps += 1
                    if current != j:
                        # 未能到达目标，跳过该 OD
                        continue
                else:
                    # 未知模式，回退到最短路径
                    path = nx.shortest_path(G, i, j, weight=weight_func)
            except nx.NetworkXNoPath:
                continue
            for u, v in zip(path[:-1], path[1:]):
                if G.is_multigraph():
                    # 选择第一个可用的 parallel edge key
                    try:
                        k = next(iter(G[u][v]))
                        edge_key = (u, v, k)
                    except Exception:
                        # 回退到无 key 的表示
                        edge_key = (u, v)
                else:
                    edge_key = (u, v) if (u, v) in D else (v, u)
                edge_flow[edge_key] += f
        # Update D and pheromone
        for e in tqdm(D, desc="Update D/Pheromone", unit="edge", leave=False):
            D[e] += (abs(edge_flow[e]) - alpha * D[e]) * 0.1
            D[e] = max(D[e], 0.01)
            pheromone[e] = 0.7 * pheromone[e] + 0.3 * (edge_flow[e] + G.edges[e]["free_speed"])
        # Prune low D edges
        to_prune = [e for e, dval in D.items() if dval < 0.05 and pheromone[e] < 1.0]
        for e in to_prune:
            D[e] = 0.01
    # Step 5: Metrics
    edge_metrics = {}
    # 遍历带 key 的边以确保一致性
    if G.is_multigraph():
        edges_iter = list(G.edges(keys=True))
    else:
        edges_iter = list(G.edges)
    for e in tqdm(edges_iter, desc="Edge Metrics", unit="edge"):
        flow = edge_flow.get(e, 0.0)
        cap = G.edges[e]["capacity"]
        v_free = G.edges[e]["free_speed"]
        v = v_free * (1 - min(flow / cap, 1.0))
        edge_metrics[e] = {
            "flow": flow,
            "capacity": cap,
            "v_free": v_free,
            "speed": v,
            "congestion": 1 - (v / v_free)
        }
    # Debugging info: 总的 OD 需求和边流量
    try:
        total_od = sum(od_flows.values())
    except Exception:
        total_od = 0.0
    total_edge_flow = sum(m["flow"] for m in edge_metrics.values())
    print(f"[模拟调试] OD 对数: {len(od_flows)}, OD 总量: {total_od:.3f}, 边总流量: {total_edge_flow:.3f}")
    # Step 6: Project to grid
    grid_flow = np.zeros((grid_size, grid_size))
    grid_cong = np.zeros((grid_size, grid_size))
    pos = _get_node_positions(G)
    # 人流在道路周围有一定扩散（膨胀）
    from scipy.ndimage import gaussian_filter
    for e, m in edge_metrics.items():
        if len(e) == 2:
            u, v = e
        elif len(e) == 3:
            u, v, _ = e
        else:
            raise ValueError(f"Edge tuple unpack error: {e}")
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        for t in np.linspace(0, 1, 20):
            x = x0 * (1 - t) + x1 * t
            y = y0 * (1 - t) + y1 * t
            ix = int(x * (grid_size - 1))
            iy = int(y * (grid_size - 1))
            if 0 <= ix < grid_size and 0 <= iy < grid_size:
                grid_flow[iy, ix] += m["flow"]
                grid_cong[iy, ix] += m["congestion"]
    # 对人流和拥堵热力图做一次空间膨胀（高斯模糊），模拟人流在道路周围扩散
    grid_flow = gaussian_filter(grid_flow, sigma=gaussian_sigma)
    grid_cong = gaussian_filter(grid_cong, sigma=gaussian_sigma)
    # 若网格全部为0（模型未产生流量），添加微量噪声以便可视化并给出提示
    if np.allclose(grid_flow, 0) and np.allclose(grid_cong, 0):
        print("[模拟警告] 投影到网格后无流量，添加微量噪声以便调试热力图。")
        rng = np.random.default_rng(seed=42)
        grid_flow += rng.random(grid_flow.shape) * 1e-3
        grid_cong += rng.random(grid_cong.shape) * 1e-3
    # Normalize
    flow_norm = (grid_flow - grid_flow.min()) / (np.ptp(grid_flow) + 1e-6)
    cong_norm = (grid_cong - grid_cong.min()) / (np.ptp(grid_cong) + 1e-6)
    grid_hybrid = 0.6 * flow_norm + 0.4 * cong_norm
    grid_metrics = {
        "flow": flow_norm,
        "congestion": cong_norm,
        "hybrid": grid_hybrid
    }
    # Step 8: Summary stats
    max_cong = max(m["congestion"] for m in edge_metrics.values())
    busiest = max(edge_metrics.items(), key=lambda x: x[1]["flow"])[0]
    avg_speed = np.mean([m["speed"] for m in edge_metrics.values()])
    summary = {
        "max_congestion": max_cong,
        "busiest_edge": busiest,
        "average_speed": avg_speed
    }
    return edge_metrics, grid_metrics, summary

def _get_node_positions(G):
    # Try to get lat/lon, else use spring layout
    if all("x" in G.nodes[n] and "y" in G.nodes[n] for n in G.nodes):
        xs = np.array([G.nodes[n]["x"] for n in G.nodes])
        ys = np.array([G.nodes[n]["y"] for n in G.nodes])
        xs = (xs - xs.min()) / (np.ptp(xs) + 1e-6)
        ys = (ys - ys.min()) / (np.ptp(ys) + 1e-6)
        return {n: (xs[i], ys[i]) for i, n in enumerate(G.nodes)}
    else:
        pos = nx.spring_layout(G, seed=42, dim=2)
        xs = np.array([p[0] for p in pos.values()])
        ys = np.array([p[1] for p in pos.values()])
        xs = (xs - xs.min()) / (np.ptp(xs) + 1e-6)
        ys = (ys - ys.min()) / (np.ptp(ys) + 1e-6)
        return {n: (xs[i], ys[i]) for i, n in enumerate(G.nodes)}
