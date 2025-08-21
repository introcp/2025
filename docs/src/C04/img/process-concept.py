import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties

# --- Setup ---
fig, ax = plt.subplots(figsize=(14, 9))
ax.set_aspect('equal')
ax.set_xlim(0, 140)
ax.set_ylim(0, 90)
ax.axis('off')
fig.patch.set_facecolor('#f0f0f0')

# --- Fonts ---
title_font = FontProperties(family='sans-serif', style='normal', weight='bold', size=20)
subtitle_font = FontProperties(family='sans-serif', style='normal', weight='bold', size=14)
body_font = FontProperties(family='sans-serif', style='normal', size=10)
label_font = FontProperties(family='sans-serif', style='normal', size=9)

# --- Colors ---
CPU_COLOR = '#4A90E2'
RAM_COLOR = '#50E3C2'
STORAGE_COLOR = '#F5A623'
PROCESS_COLORS = ['#B8E986', '#F8E71C', '#7ED321', '#E0E0E0']
ARROW_COLOR = '#4A4A4A'
TEXT_COLOR = '#333333'
SHADOW_COLOR = '#000000'

# --- Helper Function for Drop Shadow ---
def draw_shadow(patch):
    shadow = patches.FancyBboxPatch((patch.get_x() + 1, patch.get_y() - 1),
                                    patch.get_width(), patch.get_height(),
                                    boxstyle=patch.get_boxstyle(),
                                    facecolor=SHADOW_COLOR,
                                    edgecolor='none',
                                    alpha=0.2,
                                    zorder=patch.zorder - 1)
    ax.add_patch(shadow)

# --- Main Components ---
# RAM
ram_rect = patches.FancyBboxPatch((40, 10), 60, 70, boxstyle="round,pad=0.1", fc=RAM_COLOR, ec='white', lw=2, zorder=2)
ax.add_patch(ram_rect)
draw_shadow(ram_rect)
ax.text(70, 82, "Memory (RAM)", fontproperties=subtitle_font, ha='center', color='white')

# CPU
cpu_rect = patches.FancyBboxPatch((110, 40), 25, 15, boxstyle="round,pad=0.1", fc=CPU_COLOR, ec='white', lw=2, zorder=2)
ax.add_patch(cpu_rect)
draw_shadow(cpu_rect)
ax.text(122.5, 47.5, "CPU", fontproperties=subtitle_font, ha='center', color='white')

# Storage
storage_rect = patches.FancyBboxPatch((5, 40), 25, 15, boxstyle="round,pad=0.1", fc=STORAGE_COLOR, ec='white', lw=2, zorder=2)
ax.add_patch(storage_rect)
draw_shadow(storage_rect)
ax.text(17.5, 47.5, "Storage", fontproperties=subtitle_font, ha='center', color='white')

# --- Processes in RAM ---
processes = [
    {'name': 'Browser', 'pid': '1234', 'state': 'Running', 'pos': (55, 60), 'color': PROCESS_COLORS[0]},
    {'name': 'Editor', 'pid': '5678', 'state': 'Ready', 'pos': (75, 60), 'color': PROCESS_COLORS[1]},
    {'name': 'Music', 'pid': '9012', 'state': 'Blocked', 'pos': (55, 40), 'color': PROCESS_COLORS[2]},
    {'name': 'OS Kernel', 'pid': '1', 'state': 'System', 'pos': (75, 40), 'color': PROCESS_COLORS[3]},
]

for p in processes:
    proc_rect = patches.FancyBboxPatch(p['pos'], 18, 12, boxstyle="round,pad=0.05", fc=p['color'], ec='white', lw=1.5, zorder=3)
    ax.add_patch(proc_rect)
    draw_shadow(proc_rect)
    ax.text(p['pos'][0] + 9, p['pos'][1] + 8, p['name'], fontproperties=body_font, ha='center', weight='bold', color=TEXT_COLOR)
    ax.text(p['pos'][0] + 9, p['pos'][1] + 4, f"PID: {p['pid']}", fontproperties=label_font, ha='center', color=TEXT_COLOR)

# --- Programs on Storage ---
programs = [
    {'name': 'chrome.exe', 'pos': (17.5, 43)},
    {'name': 'code.exe', 'pos': (17.5, 38)},
]
for prog in programs:
    ax.text(prog['pos'][0], prog['pos'][1] + 5, prog['name'], fontproperties=body_font, ha='center', color=TEXT_COLOR)

# --- Arrows and Labels ---
# Storage -> RAM (Load)
ax.annotate("", xy=(53, 66), xytext=(30, 47.5),
            arrowprops=dict(arrowstyle="->,head_width=0.6,head_length=0.8",
                            color=ARROW_COLOR, lw=2, shrinkA=5, shrinkB=5,
                            connectionstyle="arc3,rad=0.3"))
ax.text(38, 58, "Load Program", fontproperties=body_font, ha='center', color=TEXT_COLOR, rotation=25)

# RAM -> CPU (Execute)
ax.annotate("", xy=(108, 47.5), xytext=(73, 66),
            arrowprops=dict(arrowstyle="->,head_width=0.6,head_length=0.8",
                            color=ARROW_COLOR, lw=2, shrinkA=5, shrinkB=5,
                            connectionstyle="arc3,rad=-0.3"))
ax.text(95, 58, "Execute", fontproperties=body_font, ha='center', color=TEXT_COLOR, rotation=-25)

# --- Process State Legend ---
state_legend = {
    'Running': 'Executing on CPU',
    'Ready': 'Waiting for CPU',
    'Blocked': 'Waiting for I/O'
}
y_offset = 25
ax.text(115, y_offset + 8, "Process States", fontproperties=subtitle_font, ha='left', color=TEXT_COLOR)
for state, desc in state_legend.items():
    ax.text(115, y_offset, f"• {state}: {desc}", fontproperties=body_font, ha='left', color=TEXT_COLOR)
    y_offset -= 4

# --- Save ---
plt.savefig('process-concept.png', dpi=300, bbox_inches='tight', pad_inches=0.1, facecolor=fig.patch.get_facecolor())
plt.close()

print('Process concept diagram created')