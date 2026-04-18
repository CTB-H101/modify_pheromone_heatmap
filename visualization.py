# visualization.py
"""
Heatmap generation and visualization using matplotlib.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter
import networkx as nx
from graph import build_campus_graph
import contextily as ctx

def generate_heatmaps(grid_metrics, threshold=0.02, alpha=0.75):
    titles = [
        "Human Flow Heatmap",
        "Congestion Heatmap",
        "Hybrid Heatmap"
    ]
    keys = ["flow", "congestion", "hybrid"]
    # 获取底图结构
    G, _ = build_campus_graph()
    pos = _get_node_positions_for_vis(G)
    # 判断是否为 OSM 模式（节点有 x/y 属性）
    is_osm = all("x" in G.nodes[n] and "y" in G.nodes[n] for n in G.nodes)

    for i, key in enumerate(keys):
        data = grid_metrics[key]
        # 归一化到[0,1]
        data_norm = (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data) + 1e-9)
        data_smooth = gaussian_filter(data_norm, sigma=2)

        # 一、不带底图的热力图（像素坐标）
        fig_n, ax_n = plt.subplots(figsize=(7, 6))
        extent_px = (0, data.shape[1], 0, data.shape[0])
        # 使用不带末端白色的配色（inferno），避免全白表示饱和
        cmap = plt.get_cmap("inferno").copy()
        cmap.set_bad(color=(0, 0, 0, 0))
        # 计算色阶上限，使用 98 百分位以避免极端值撑满色阶
        vmax_px = float(np.nanpercentile(data_smooth, 98))
        if vmax_px <= 0:
            vmax_px = float(data_smooth.max() if data_smooth.max() > 0 else 1e-6)
        # 低于阈值的像素在叠加时应为全透明
        masked_px = np.ma.masked_where(data_smooth <= threshold, data_smooth)
        im_n = ax_n.imshow(masked_px, cmap=cmap, origin="lower", vmin=0, vmax=vmax_px, extent=extent_px, zorder=1, alpha=alpha)
        # 调试信息
        if np.nansum(data_smooth) == 0:
            print(f"[热力图警告] '{key}' 数据全为零，输出将为空白图像。")
        ax_n.set_xlim(0, data.shape[1])
        ax_n.set_ylim(0, data.shape[0])
        ax_n.set_xlabel("X")
        ax_n.set_ylabel("Y")
        try:
            xt = np.linspace(0, data.shape[1], 5)
            yt = np.linspace(0, data.shape[0], 5)
            ax_n.set_xticks(xt)
            ax_n.set_yticks(yt)
            ax_n.set_xticklabels([f"{int(v)}" for v in xt])
            ax_n.set_yticklabels([f"{int(v)}" for v in yt])
        except Exception:
            pass
        # 绘制网络结构（像素坐标）
        for edge in G.edges:
            if len(edge) == 2:
                u, v = edge
            elif len(edge) == 3:
                u, v, _ = edge
            else:
                raise ValueError(f"Edge tuple unpack error: {edge}")
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            ax_n.plot([x0 * data.shape[1], x1 * data.shape[1]], [y0 * data.shape[0], y1 * data.shape[0]], color="#222222", alpha=0.5, linewidth=0.5, zorder=2)
        _draw_pixel_scalebar(ax_n, data.shape, fraction=0.2)
        plt.colorbar(im_n, ax=ax_n, label="Value")
        plt.title(f"{titles[i]} (no basemap)")
        plt.tight_layout()
        out_no = f"heatmap_{key}_no_basemap.png"
        # 保存为带透明通道的 PNG，使阈值以下的区域真正透明
        fig_n.savefig(out_no, dpi=200, transparent=True)
        plt.close(fig_n)

        # 二、带底图的热力图（经纬度）
        if is_osm:
            fig_b, ax_b = plt.subplots(figsize=(7, 6))
            xs = np.array([G.nodes[n]["x"] for n in G.nodes])
            ys = np.array([G.nodes[n]["y"] for n in G.nodes])
            minx, maxx = xs.min(), xs.max()
            miny, maxy = ys.min(), ys.max()
            ax_b.set_xlim(minx, maxx)
            ax_b.set_ylim(miny, maxy)
            # 尝试加载底图（不指定 provider，让 contextily 选择默认可兼容更多版本）
            try:
                ctx.add_basemap(ax_b, crs="EPSG:4326", zoom=16, alpha=1.0)
            except Exception as e:
                print("[地图底图加载失败]", e)
            extent = (minx, maxx, miny, maxy)
            # 带底图使用相同的色阶上限
            vmax_geo = float(np.nanpercentile(data_smooth, 98))
            if vmax_geo <= 0:
                vmax_geo = float(data_smooth.max() if data_smooth.max() > 0 else 1e-6)
            im_b = ax_b.imshow(masked_px, cmap=cmap, origin="lower", vmin=0, vmax=vmax_geo, extent=extent, zorder=2, alpha=alpha)
            for edge in G.edges:
                if len(edge) == 2:
                    u, v = edge
                elif len(edge) == 3:
                    u, v, _ = edge
                else:
                    raise ValueError(f"Edge tuple unpack error: {edge}")
                x0, y0 = G.nodes[u]["x"], G.nodes[u]["y"]
                x1, y1 = G.nodes[v]["x"], G.nodes[v]["y"]
                ax_b.plot([x0, x1], [y0, y1], color="#222222", alpha=0.5, linewidth=0.5, zorder=3)
            ax_b.set_xlabel("Longitude")
            ax_b.set_ylabel("Latitude")
            _draw_scalebar(ax_b, minx, maxx, miny, maxy)
            plt.colorbar(im_b, ax=ax_b, label="Value")
            plt.title(f"{titles[i]} (with basemap)")
            plt.tight_layout()
            out_with = f"heatmap_{key}_with_basemap.png"
            fig_b.savefig(out_with, dpi=200)
            plt.close(fig_b)
        else:
            # 非 OSM 模式，仅输出 no-basemap 版本
            pass
def _draw_scalebar(ax, minx, maxx, miny, maxy, target_meters=None):
    """Draw a simple scalebar (meters) on a lon/lat axes.
    Uses approximate conversion at the central latitude.
    """
    try:
        import math
        # 中心经度/纬度
        center_lat = (miny + maxy) / 2.0
        # 近似：经度一度对应的米数（取决于纬度）
        meters_per_deg_lon = 111320.0 * math.cos(math.radians(center_lat))
        # 目标刻度长度选择（单位：米）
        axis_width_deg = maxx - minx
        axis_width_m = axis_width_deg * meters_per_deg_lon
        # 选择一个好看的刻度（50,100,200,500,1000）
        nice = [50, 100, 200, 500, 1000, 2000, 5000]
        if target_meters is None:
            # 目标为轴宽的约1/6
            target = axis_width_m / 6.0
            length_m = min(nice, key=lambda v: abs(v - target))
        else:
            length_m = target_meters
        # 转换为经度度数
        dx_deg = length_m / meters_per_deg_lon if meters_per_deg_lon != 0 else 0
        # 放置在图的左下角，留出边距
        x0 = minx + 0.02 * (maxx - minx)
        y0 = miny + 0.02 * (maxy - miny)
        x1 = x0 + dx_deg
        # 画线和文本
        ax.plot([x0, x1], [y0, y0], color='k', linewidth=3, solid_capstyle='butt', zorder=10)
        ax.plot([x0, x0], [y0 - 0.002 * (maxy - miny), y0 + 0.002 * (maxy - miny)], color='k', linewidth=2, zorder=10)
        ax.plot([x1, x1], [y0 - 0.002 * (maxy - miny), y0 + 0.002 * (maxy - miny)], color='k', linewidth=2, zorder=10)
        ax.text((x0 + x1) / 2.0, y0 + 0.004 * (maxy - miny), f"{int(length_m)} m", ha='center', va='bottom', fontsize=9, zorder=10, backgroundcolor='white')
    except Exception:
        pass


def _draw_pixel_scalebar(ax, shape, fraction=0.2):
    """Draw a simple pixel scalebar for grid images.
    shape: (rows, cols)
    fraction: desired fraction of width for scalebar
    """
    try:
        rows, cols = shape
        length_px = int(cols * fraction)
        x0 = 0 + cols * 0.02
        y0 = 0 + rows * 0.02
        x1 = x0 + length_px
        ax.plot([x0, x1], [y0, y0], color='k', linewidth=3, solid_capstyle='butt', zorder=10)
        ax.plot([x0, x0], [y0 - rows * 0.01, y0 + rows * 0.01], color='k', linewidth=2, zorder=10)
        ax.plot([x1, x1], [y0 - rows * 0.01, y0 + rows * 0.01], color='k', linewidth=2, zorder=10)
        ax.text((x0 + x1) / 2.0, y0 + rows * 0.03, f"{length_px} px", ha='center', va='bottom', fontsize=9, zorder=10, backgroundcolor='white')
    except Exception:
        pass


def _get_node_positions_for_vis(G):
    """Return node positions normalized to [0,1] for visualization.
    If nodes have 'x'/'y' (OSM), normalize their lon/lat to [0,1]; otherwise use spring_layout.
    """
    if all("x" in G.nodes[n] and "y" in G.nodes[n] for n in G.nodes):
        xs = np.array([G.nodes[n]["x"] for n in G.nodes])
        ys = np.array([G.nodes[n]["y"] for n in G.nodes])
        xs_n = (xs - xs.min()) / (np.ptp(xs) + 1e-6)
        ys_n = (ys - ys.min()) / (np.ptp(ys) + 1e-6)
        return {n: (xs_n[i], ys_n[i]) for i, n in enumerate(G.nodes)}
    else:
        pos = nx.spring_layout(G, seed=42, dim=2)
        xs = np.array([p[0] for p in pos.values()])
        ys = np.array([p[1] for p in pos.values()])
        xs_n = (xs - xs.min()) / (np.ptp(xs) + 1e-6)
        ys_n = (ys - ys.min()) / (np.ptp(ys) + 1e-6)
        return {n: (xs_n[i], ys_n[i]) for i, n in enumerate(G.nodes)}


def print_summary_stats(summary):
    print("==== Simulation Summary ====")
    print(f"Max congestion: {summary['max_congestion']:.3f}")
    print(f"Busiest edge: {summary['busiest_edge']}")
    print(f"Average speed: {summary['average_speed']:.3f} m/s")


