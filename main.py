# main.py
"""
Entry point for Harvard campus pedestrian flow simulation and heatmap generation.
"""
from graph import build_campus_graph
from simulation import run_simulation
from visualization import generate_heatmaps, print_summary_stats

# 全局可配置超参数（可在此修改以调参）
# 说明：
# - duration: 模拟总时长（单位与 timestep 一致，未深入时间步长语义时保留为实验参数）
# - timestep: 模拟时间步长（暂未用于细粒度时间推进，保留为未来扩展）
# - alpha: 更新 D 的阻尼/衰减参数（越大表示对历史占优记忆越弱）
# - epsilon: 用于重心模型中避免除零的小常数（也用于稳定数值）
# - sim_iters: 路径搜索与 D/pheromone 更新的迭代次数（迭代越多，路径收敛越明显）
# - grid_size: 投影热力图时的网格分辨率（例如 100 表示 100x100）
# - gaussian_sigma: 对投影后网格应用高斯模糊的 sigma（数值越大扩散越宽）
# - random_walker_frac: 用于在 OD 之外注入随机行人的比例（相对于 OD 对数数量）
# - random_seed: 随机数种子，便于结果复现；None 表示不固定随机性
# 可视化参数：
# - heatmap_threshold: 归一化后热力图阈值，低于该值的像素在叠加时设为完全透明，直接显示底图
# - heatmap_alpha: 热力图叠加到底图时的透明度（0.0-1.0）
CONFIG = {
    # 模拟参数
    "duration": 60,
    "timestep": 1,
    "alpha": 0.1,
    "epsilon": 1e-3,
    "sim_iters": 10,
    "grid_size": 100,
    "gaussian_sigma": 2,
    "random_walker_frac": 0.15,
    "random_seed": 42,
    # 可视化参数
    "heatmap_threshold": 0.02,  # 归一化后值，低于此值设为透明
    "heatmap_alpha": 0.75,      # 叠加透明度
}


def run_all():
    from tqdm import tqdm
    print("[1/5] 构建校园网络...")
    G, pois = build_campus_graph()

    print("[2/5] 生成OD需求（Gravity Model）...")
    # run_simulation 内部已带进度条，参数来自 CONFIG
    edge_metrics, grid_metrics, summary = run_simulation(
        G,
        pois,
        duration=CONFIG["duration"],
        timestep=CONFIG["timestep"],
        alpha=CONFIG["alpha"],
        epsilon=CONFIG["epsilon"],
        sim_iters=CONFIG["sim_iters"],
        grid_size=CONFIG["grid_size"],
        gaussian_sigma=CONFIG["gaussian_sigma"],
        random_walker_frac=CONFIG["random_walker_frac"],
        random_seed=CONFIG["random_seed"],
    )

    print("[3/5] 计算边属性与流量...")
    # run_simulation 内部已带进度条

    print("[4/5] 生成热力图...")
    for _ in tqdm(range(1), desc="Heatmap Generation"):
        generate_heatmaps(
            grid_metrics,
            threshold=CONFIG["heatmap_threshold"],
            alpha=CONFIG["heatmap_alpha"],
        )

    print("[5/5] 输出统计信息...")
    print_summary_stats(summary)

if __name__ == "__main__":
    run_all()

