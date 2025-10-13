import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import numpy as np
from math import sqrt

def plot_tetrahedron(show_axes=False, show_labels=False, elev=20, azim=45, figsize=(10, 8)):
    """
    Plot a 3D tetrahedron with customizable visibility options.

    Parameters:
    -----------
    show_axes : bool, optional (default=False)
        Whether to show axes and grid
    show_labels : bool, optional (default=False)
        Whether to show vertex labels (A, B, C, D)
    elev : float, optional (default=20)
        Elevation viewing angle in degrees
    azim : float, optional (default=45)
        Azimuthal viewing angle in degrees
    figsize : tuple, optional (default=(8, 8))
        Figure size in inches (width, height)

    Returns:
    --------
    fig, ax : matplotlib figure and axes objects
    """

    # define vertices
    verts = np.array([
        [0, 1, -1],  # A
        [1, -1, -1],  # B
        [0, 0, 1],  # C
        [(1 - sqrt(3)), -.4, -1],  # D
    ])
    labels = ['A', 'B', 'C', 'D']

    # define faces (triplets of indices)
    faces = [
        [0, 1, 2],
        [0, 1, 3],
        [0, 2, 3],
        [1, 2, 3],
    ]

    # extract unique edges
    edges = set()
    for f in faces:
        for i in range(3):
            a, b = sorted((f[i], f[(i + 1) % 3]))
            edges.add((a, b))
    edges = list(edges)

    # explicitly list the dashed edge pairs (use sorted tuples to match 'edges')
    dashed_pairs = {(1, 3), (0, 3), (2, 3)}  # B–D and A–D dashed

    # build segment lists from edges
    dashed_segments = [[verts[a], verts[b]] for a, b in edges if (a, b) in dashed_pairs]
    solid_segments = [[verts[a], verts[b]] for a, b in edges if (a, b) not in dashed_pairs]

    # plot
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')

    # draw solid edges
    solid_lines = Line3DCollection(solid_segments, colors='k', linewidths=1.8, linestyles='solid')
    ax.add_collection3d(solid_lines)

    # draw dashed edges connected to D
    dashed_lines = Line3DCollection(dashed_segments, colors='k', linewidths=1.8, linestyles=(0, (5, 5)))
    ax.add_collection3d(dashed_lines)

    # draw black balls at vertices
    ax.scatter(verts[:, 0], verts[:, 1], verts[:, 2],
               color='black', s=70, zorder=10, depthshade=False)

    # equal aspect ratio
    max_range = (verts.max(axis=0) - verts.min(axis=0)).max() / 2.0
    mid = verts.mean(axis=0)
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)
    ax.set_box_aspect([1, 1, 1])

    # rotate view
    ax.view_init(elev=elev, azim=azim)

    # axes and grid toggle
    if show_axes:
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.grid(True)

        # set fixed axis limits and ticks
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_zlim(-1, 1)

        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
        ax.set_zticks([-1, 0, 1])
    else:
        ax.set_axis_off()

    # label toggle
    if show_labels:
        for i, (x, y, z) in enumerate(verts):
            ax.text(x, y, z, labels[i],
                    fontsize=12, fontweight='bold',
                    color='darkred',
                    ha='center', va='center')

    plt.tight_layout()
    return fig, ax


def add_text(ax, verts=None, font_size=13, font_color='black'):
    """
    Add descriptive text labels to the tetrahedron vertices with custom positioning.

    Parameters:
    -----------
    ax : matplotlib 3D axes object
        The axes to add text to
    verts : np.array, optional
        Vertex coordinates. If None, uses default tetrahedron vertices
    font_size : int, optional (default=13)
        Font size for the text labels
    font_color : str, optional (default='black')
        Color of the text labels
    """

    # define vertices if not provided
    if verts is None:
        verts = np.array([
            [0, 1, -1],  # A
            [1, -1, -1],  # B
            [0, 0, 1],  # C
            [(1 - sqrt(3)), -.4, -1],  # D
        ])

    # text labels for each vertex
    text_labels = [
        "Rules of\nthe Game",  # A
        "Resources and\nPower Dynamics",  # B
        "Actors and\nCoalitions",  # C
        "Discourses"  # D
    ]

    # custom offsets for each vertex [x_offset, y_offset, z_offset]
    offsets = [
        [-0.4, 0.1, 0],  # A - further left
        [0.5, 0, 0.25],  # B - further right
        [-0.45, 0.1, -.15],  # C - further left and down
        [.5, 0, .21]  # D
    ]

    # add text at each vertex with custom offset
    for i, (x, y, z) in enumerate(verts):
        if text_labels[i]:  # only add text if label is not empty
            offset = offsets[i]
            ax.text(x + offset[0], y + offset[1], z + offset[2],
                    text_labels[i],
                    fontsize=font_size,
                    color=font_color,
                    ha='center', va='bottom',
                    weight='bold')


# Example usage:
if __name__ == "__main__":

    # Create the tetrahedron plot
    fig, ax = plot_tetrahedron(show_labels=False)  # Can show vertex labels A, B, C, D

    # Add the descriptive text
    add_text(ax)

    plt.savefig('Figures/Figure 1 - Tetrahedron.pdf', dpi=450)
    plt.savefig('Figures/Figure 1 - Tetrahedron.png', dpi=450)

    plt.show()