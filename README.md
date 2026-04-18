# Harvard Campus Pedestrian Heatmap

本项目在哈佛校园范围内使用 OpenStreetMap（OSM）道路网络进行步行人流模拟，并导出热力图（带/不带底图）。

主要功能
- 使用真实 OSM 拓扑构建道路网络（`graph.py`）。
- 基于重力模型生成 OD 需求，结合路径选择进行人流模拟（`simulation.py`）。
- 将边流量投影到固定网格并生成热力图，支持阈值透明与 alpha 叠加（`visualization.py`）。
- 自动保存图片（不弹窗），并输出简单统计信息（`main.py`）。

快速开始

1. 安装依赖（建议使用 virtualenv 或 venv）：

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

如果项目没有 `requirements.txt`，至少需要安装：
```
pip install osmnx networkx numpy scipy matplotlib contextily xyzservices tqdm Pillow
```

2. 配置（可选）：
- 打开 `main.py`，在 `CONFIG` 中修改超参数：
  - `sim_iters`：路径迭代次数
  - `grid_size`：热力网格分辨率（例如 100）
  - `gaussian_sigma`：网格高斯模糊的 sigma
  - `heatmap_threshold`：热力图阈值，归一化后低于该值的像素将被设为透明
  - `heatmap_alpha`：热力图叠加到底图时的透明度

3. 运行：

```bash
python main.py
```

输出
- 在项目根目录生成以下文件：
  - `heatmap_flow_no_basemap.png`
  - `heatmap_flow_with_basemap.png`
  - `heatmap_congestion_no_basemap.png`
  - `heatmap_congestion_with_basemap.png`
  - `heatmap_hybrid_no_basemap.png`
  - `heatmap_hybrid_with_basemap.png`
  - `test_tile.png`（底图测试）

说明与注意事项
- 所有热力图在导出前会归一化到 [0,1] 并使用 98% 百分位作为上限，以减少极端值影响。低于 `heatmap_threshold` 的像素被掩码并在输出时透明（no-basemap 输出保存为带透明通道的 PNG）。
- 默认使用 `inferno` 配色，避免色条末端出现纯白导致误解。
- 项目依赖在线获取 OSM 瓦片（用于带底图的输出），请确保网络通畅与 contextily 可用的瓦片提供器。
- 若模拟产生的投影网格全为零，程序会临时加入极小噪声以便调试（可在 `simulation.py` 中移除以保持纯净结果）。

开发与调试
- 若需复现随机结果，请在 `main.py` 中设置 `random_seed`。
- 若希望外部编辑配置，可让我把 `CONFIG` 导出为 `config.yaml` 并在 `main.py` 中优先读取它。

许可与数据
- 本项目使用 OpenStreetMap 数据，遵循 OSM 的使用条款与许可要求。

---
如果需要，我可以：
- 生成 `requirements.txt`；
- 将 `CONFIG` 支持从 `config.yaml` 加载；
- 批量导出透明覆盖层以便在 GIS/图形软件中合成底图。
