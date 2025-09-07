import microtrax as mtx
import numpy as np
import matplotlib.pyplot as plt
import time

# Initialize experiment
mtx.init('./my_experiments')

for i in range(10):
    base_loss = 1.0 / (i + 1)
    noise = np.random.normal(0, 0.1)
    mtx.log({
        "step": i,
        "loss": max(0.01, base_loss + noise),
        "accuracy": min(1.0, i * 0.1 + np.random.normal(0, 0.02))
    })
    time.sleep(1)

# Log image (single)
img = np.random.rand(64, 64, 3)
mtx.log_images(img, step=10, labels="sample_image")

# Log image batches with labels
batch = np.random.rand(8, 3, 64, 64)  # (B, C, H, W)
labels = [0, 1, 2, 3, 4, 5, 6, 7]
mtx.log_images(batch, step=11, labels=labels)

# Log matplotlib figures
fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
mtx.log_images(fig, step=12, labels="training plot")
plt.close(fig)

# Finish experiment
mtx.finish()
