# graph.py
"""
Campus graph construction using osmnx (preferred) or synthetic fallback.
"""
import networkx as nx
import numpy as np

try:
    import osmnx as ox
    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False

# Key POI types
POI_TYPES = ["dorm", "classroom", "dining", "library"]

# Harvard campus bounding box (approximate)
HARVARD_BBOX = {
    "north": 42.378,
    "south": 42.370,
    "east": -71.110,
    "west": -71.120
}


def build_campus_graph():
    """
    Build the campus graph and assign POIs and attributes.
    Returns:
        G: networkx.Graph
        pois: dict of node_id -> {type, weight}
    """
    if not OSMNX_AVAILABLE:
        raise ImportError("osmnx 未安装，无法获取真实哈佛校园步行网络。请先安装 osmnx。");
    try:
        bbox = (HARVARD_BBOX["west"], HARVARD_BBOX["south"], HARVARD_BBOX["east"], HARVARD_BBOX["north"])
        G = ox.graph_from_bbox(bbox, network_type="walk")
        # osmnx 2.x 默认已简化，无需再次 simplify_graph
        # Assign edge attributes
        for u, v, d in G.edges(data=True):
            d["length"] = d.get("length", 30.0)
            d["capacity"] = np.random.randint(20, 60)  # people/min
            d["free_speed"] = np.random.uniform(1.0, 1.5)  # m/s
        # Select POIs
        nodes = list(G.nodes)
        np.random.seed(42)
        pois = {}
        for t in POI_TYPES:
            for _ in range(3):
                n = np.random.choice(nodes)
                pois[n] = {"type": t, "weight": np.random.uniform(1, 3)}
        return G, pois
    except Exception as e:
        raise RuntimeError(f"OSM 数据获取失败: {e}\n请检查网络连接或 OSMNX 配置。")
