# test_tile.py
"""
测试 contextily 是否能正常获取并显示哈佛校园区域的地图瓦片。
"""
import matplotlib.pyplot as plt
import contextily as ctx

# 哈佛主校区地界
bbox = (-71.120, 42.370, -71.110, 42.378)
fig, ax = plt.subplots(figsize=(7, 6))
ax.set_xlim(bbox[0], bbox[2])
ax.set_ylim(bbox[1], bbox[3])
providers = [
    # ctx.providers.Stamen.TonerLite,
    ctx.providers.OpenStreetMap.Mapnik,
    ctx.providers.CartoDB.Positron,
    ctx.providers.OpenTopoMap,
]

success = False
for provider in providers:
    try:
        ctx.add_basemap(ax, crs="EPSG:4326", source=provider, zoom=16, alpha=0.8)
        print(f"底图加载成功: {provider}")
        success = True
        break
    except Exception as e:
        print(f"底图加载失败: {provider}，原因: {e}")

if not success:
    print("所有 provider 均加载失败！")

plt.title("Contextily Tile Fallback Test")
plt.tight_layout()
plt.savefig("test_tile.png", dpi=150)
plt.show()
