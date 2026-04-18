from PIL import Image
import numpy as np
files = [
    'heatmap_flow_no_basemap.png',
    'heatmap_flow_with_basemap.png',
    'heatmap_congestion_no_basemap.png',
    'heatmap_congestion_with_basemap.png',
    'heatmap_hybrid_no_basemap.png',
    'heatmap_hybrid_with_basemap.png',
]
for f in files:
    try:
        im = Image.open(f).convert('L')
        a = np.array(im)
        print(f, 'min', int(a.min()), 'max', int(a.max()), 'mean', float(a.mean()))
    except Exception as e:
        print('skip', f, e)
