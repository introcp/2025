import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Create filesystem tree diagram
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
ax.set_xlim(0.5, 9.5)
ax.set_ylim(0.5, 9.5)
ax.axis('off')

# Define colors
root_color = '#2E86AB'
folder_color = '#A23B72'
file_color = '#F18F01'

# Root
root = FancyBboxPatch((4, 8.5), 2, 0.8, boxstyle='round,pad=0.1', 
                      facecolor=root_color, edgecolor='black', linewidth=2)
ax.add_patch(root)
ax.text(5, 8.9, 'Root (/)', ha='center', va='center', fontsize=12, fontweight='bold', color='white')

# Level 1 folders
folders_l1 = [
    {'name': 'System', 'x': 1, 'y': 6.5},
    {'name': 'Applications', 'x': 3.5, 'y': 6.5},
    {'name': 'Users', 'x': 6, 'y': 6.5},
    {'name': 'Library', 'x': 8.5, 'y': 6.5}
]

for folder in folders_l1:
    box = FancyBboxPatch((folder['x']-0.6, folder['y']), 1.2, 0.6, boxstyle='round,pad=0.05',
                         facecolor=folder_color, edgecolor='black')
    ax.add_patch(box)
    ax.text(folder['x'], folder['y']+0.3, folder['name'], ha='center', va='center', fontsize=10, color='white')
    # Draw line from root
    ax.plot([5, folder['x']], [8.5, folder['y']+0.6], 'k-', linewidth=1)

# Level 2 folders under Users
users_folders = [
    {'name': 'alice', 'x': 5, 'y': 4.5},
    {'name': 'bob', 'x': 7, 'y': 4.5}
]

for folder in users_folders:
    box = FancyBboxPatch((folder['x']-0.5, folder['y']), 1, 0.5, boxstyle='round,pad=0.05',
                         facecolor=folder_color, edgecolor='black')
    ax.add_patch(box)
    ax.text(folder['x'], folder['y']+0.25, folder['name'], ha='center', va='center', fontsize=9, color='white')
    # Draw line from Users
    ax.plot([6, folder['x']], [6.5, folder['y']+0.5], 'k-', linewidth=1)

# Level 3 folders under alice
alice_folders = [
    {'name': 'Documents', 'x': 3.5, 'y': 2.5},
    {'name': 'Pictures', 'x': 4.8, 'y': 2.5},
    {'name': 'Downloads', 'x': 6.1, 'y': 2.5}
]

for folder in alice_folders:
    box = FancyBboxPatch((folder['x']-0.4, folder['y']), 0.8, 0.4, boxstyle='round,pad=0.03',
                         facecolor=folder_color, edgecolor='black')
    ax.add_patch(box)
    ax.text(folder['x'], folder['y']+0.2, folder['name'], ha='center', va='center', fontsize=8, color='white')
    # Draw line from alice
    ax.plot([5, folder['x']], [4.5, folder['y']+0.4], 'k-', linewidth=1)

# Add some files
files = [
    {'name': 'report.txt', 'x': 3.5, 'y': 1},
    {'name': 'photo.jpg', 'x': 4.8, 'y': 1},
    {'name': 'setup.exe', 'x': 6.1, 'y': 1}
]

for file in files:
    box = FancyBboxPatch((file['x']-0.3, file['y']), 0.6, 0.3, boxstyle='round,pad=0.02',
                         facecolor=file_color, edgecolor='black')
    ax.add_patch(box)
    ax.text(file['x'], file['y']+0.15, file['name'], ha='center', va='center', fontsize=7, color='white')
    # Draw line from parent folder
    parent_x = file['x']
    ax.plot([parent_x, file['x']], [2.5, file['y']+0.3], 'k-', linewidth=1)

# plt.title('File System Hierarchical Structure', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('filesystem-tree.png', dpi=300, bbox_inches='tight')
plt.close()

print('Filesystem tree diagram created')