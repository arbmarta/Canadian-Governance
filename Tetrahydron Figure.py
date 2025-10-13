import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

# vertices of a regular-ish tetrahedron
verts = np.array([
    [1, 1, 1],
    [-1, -1, 1],
    [-1, 1, -1],
    [1, -1, -1],
])

faces = [
    [0, 1, 2],
    [0, 1, 3],
    [0, 2, 3],
    [1, 2, 3],
]

fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(111, projection='3d')
poly = Poly3DCollection([verts[f] for f in faces], alpha=0.6, edgecolor='k')
ax.add_collection3d(poly)

# plot vertices
ax.scatter(verts[:,0], verts[:,1], verts[:,2], s=50, color='k')

# set equal aspect
max_range = (verts.max(axis=0) - verts.min(axis=0)).max() / 2.0
mid = verts.mean(axis=0)
ax.set_xlim(mid[0]-max_range, mid[0]+max_range)
ax.set_ylim(mid[1]-max_range, mid[1]+max_range)
ax.set_zlim(mid[2]-max_range, mid[2]+max_range)

# remove grid and axes
ax.grid(False)
ax.set_axis_off()

plt.show()
