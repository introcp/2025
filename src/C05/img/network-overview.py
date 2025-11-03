#!/usr/bin/env python3
"""
Generate network overview diagram
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Title
ax.text(5, 9.5, 'Computer Network Overview', fontsize=24, weight='bold', ha='center')

# Draw nodes (computers)
nodes = [
    (2, 7, 'Computer 1'),
    (8, 7, 'Computer 2'),
    (2, 3, 'Server'),
    (8, 3, 'Phone'),
    (5, 5, 'Router')
]

for x, y, label in nodes:
    if 'Router' in label:
        # Router (pentagon shape)
        pentagon = mpatches.RegularPolygon((x, y), 5, radius=0.6, 
                                          facecolor='orange', edgecolor='black', linewidth=2)
        ax.add_patch(pentagon)
    else:
        # Devices (rectangles)
        rect = FancyBboxPatch((x-0.5, y-0.4), 1, 0.8, boxstyle="round,pad=0.1",
                             facecolor='lightblue', edgecolor='black', linewidth=2)
        ax.add_patch(rect)
    
    ax.text(x, y-1, label, fontsize=12, ha='center', weight='bold')

# Draw connections (links)
connections = [
    (2, 7, 5, 5),  # Computer 1 to Router
    (8, 7, 5, 5),  # Computer 2 to Router
    (2, 3, 5, 5),  # Server to Router
    (8, 3, 5, 5),  # Phone to Router
]

for x1, y1, x2, y2 in connections:
    arrow = FancyArrowPatch((x1, y1-0.5), (x2, y2+0.5),
                          arrowstyle='-', linewidth=2, color='green',
                          connectionstyle="arc3,rad=0")
    ax.add_patch(arrow)

# Add legend
legend_elements = [
    mlines.Line2D([0], [0], marker='s', color='w', markerfacecolor='lightblue', 
                  markersize=15, label='Node (Device)', markeredgecolor='black', markeredgewidth=2),
    mlines.Line2D([0], [0], color='green', linewidth=2, label='Link (Connection)'),
    mlines.Line2D([0], [0], marker='p', color='w', markerfacecolor='orange', 
                  markersize=15, label='Router', markeredgecolor='black', markeredgewidth=2)
]
ax.legend(handles=legend_elements, loc='lower center', fontsize=11, ncol=3)

# Add data flow annotation
ax.annotate('', xy=(7.5, 6.5), xytext=(2.5, 6.5),
            arrowprops=dict(arrowstyle='->', lw=2, color='red'))
ax.text(5, 6.8, 'Data Flow', fontsize=11, ha='center', color='red', weight='bold')

plt.tight_layout()
plt.savefig('network-overview.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Generated network-overview.png")
