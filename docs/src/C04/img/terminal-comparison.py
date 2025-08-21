import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

# Create terminal comparison diagram
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))

# Windows Command Prompt
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.axis('off')

# Windows terminal window
win_terminal = Rectangle((1, 2), 8, 6, facecolor='black', edgecolor='gray', linewidth=2)
ax1.add_patch(win_terminal)

# Windows title bar
win_titlebar = Rectangle((1, 7.5), 8, 0.5, facecolor='#0078d4', edgecolor='gray')
ax1.add_patch(win_titlebar)
ax1.text(5, 7.75, 'Command Prompt', ha='center', va='center', fontsize=10, color='white', fontweight='bold')

# Windows terminal content
win_commands = [
    'C:\\\\Users\\\\Alice> dir',
    ' Volume in drive C has no label.',
    ' Directory of C:\\\\Users\\\\Alice',
    '',
    '21/08/2025  15:00    <DIR>          Documents',
    '21/08/2025  15:00    <DIR>          Pictures',
    '21/08/2025  15:00    <DIR>          Downloads',
    '               0 File(s)              0 bytes',
    '               3 Dir(s)  500,000,000,000 bytes free',
    '',
    'C:\\\\Users\\\\Alice> _'
]

y_pos = 7
for cmd in win_commands:
    if cmd.startswith('C:\\\\Users\\\\Alice>'):
        ax1.text(1.2, y_pos, cmd, ha='left', va='center', fontsize=8, color='white', fontfamily='monospace')
    else:
        ax1.text(1.2, y_pos, cmd, ha='left', va='center', fontsize=8, color='#c0c0c0', fontfamily='monospace')
    y_pos -= 0.4

ax1.text(5, 1.7, 'Windows Command Prompt', ha='center', va='center', fontsize=18, fontweight='bold')

# macOS Terminal
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.axis('off')

# macOS terminal window
mac_terminal = Rectangle((1, 2), 8, 6, facecolor='#1d1d1d', edgecolor='gray', linewidth=2)
ax2.add_patch(mac_terminal)

# macOS title bar
mac_titlebar = Rectangle((1, 7.5), 8, 0.5, facecolor='#3c3c3c', edgecolor='gray')
ax2.add_patch(mac_titlebar)

# macOS traffic lights
colors = ['#ff5f56', '#ffbd2e', '#27ca3f']
for i, color in enumerate(colors):
    circle = plt.Circle((1.5 + i*0.3, 7.75), 0.08, facecolor=color, edgecolor='darkgray')
    ax2.add_patch(circle)

ax2.text(5, 7.75, 'Terminal', ha='center', va='center', fontsize=10, color='white', fontweight='bold')

# macOS terminal content
mac_commands = [
    'alice@MacBook-Pro ~ % ls -la',
    'total 24',
    'drwxr-xr-x   6 alice  staff   192 Aug 21 15:00 .',
    'drwxr-xr-x   3 root   admin    96 Aug 21 15:00 ..',
    'drwx------   3 alice  staff    96 Aug 21 15:00 Documents',
    'drwx------   3 alice  staff    96 Aug 21 15:00 Pictures',
    'drwx------   3 alice  staff    96 Aug 21 15:00 Downloads',
    'drwx------   3 alice  staff    96 Aug 21 15:00 Desktop',
    '',
    'alice@MacBook-Pro ~ % _'
]

y_pos = 7
for cmd in mac_commands:
    if cmd.startswith('alice@MacBook-Pro'):
        ax2.text(1.2, y_pos, cmd, ha='left', va='center', fontsize=8, color='#00ff00', fontfamily='monospace')
    else:
        ax2.text(1.2, y_pos, cmd, ha='left', va='center', fontsize=8, color='white', fontfamily='monospace')
    y_pos -= 0.4

ax2.text(5, 1.7, 'macOS Terminal', ha='center', va='center', fontsize=18, fontweight='bold')

#plt.tight_layout()
plt.savefig('terminal-comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print('Terminal comparison diagram created')