# test_osmnx.py
"""
测试 osmnx 是否能正常下载和构建哈佛校园步行网络。
"""
import osmnx as ox

# 哈佛主校区地界
bbox = (-71.120, 42.370, -71.110, 42.378)
try:
    print("osmnx 版本:", ox.__version__)
    print("开始下载哈佛校园步行网络...")
    G = ox.graph_from_bbox(bbox, network_type="walk")
    print("节点数:", len(G.nodes))
    print("边数:", len(G.edges))
    print("图类型:", type(G))
    print("是否有向:", G.is_directed())
    print("测试成功！")
except Exception as e:
    print("osmnx 测试失败：", e)
