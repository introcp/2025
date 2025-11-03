#!/usr/bin/env python3
"""
Generate TCP/IP Stack diagram
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(10, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Title
ax.text(5, 11.5, 'TCP/IP Protocol Stack', fontsize=24, weight='bold', ha='center')

# Define layers
layers = [
    (4, 'Application Layer', 'HTTP, HTTPS, FTP, SMTP, DNS, SSH', '#FF6B6B'),
    (3, 'Transport Layer', 'TCP, UDP', '#4ECDC4'),
    (2, 'Internet Layer', 'IP, ICMP, ARP', '#45B7D1'),
    (1, 'Network Access Layer', 'Ethernet, WiFi, PPP', '#96CEB4')
]

y_start = 9
layer_height = 1.5
layer_spacing = 0.3

for layer_num, layer_name, protocols, color in layers:
    y = y_start - (4 - layer_num) * (layer_height + layer_spacing)
    
    # Draw layer box
    rect = mpatches.FancyBboxPatch((1, y), 8, layer_height, 
                                   boxstyle="round,pad=0.05",
                                   facecolor=color, edgecolor='black', 
                                   linewidth=3, alpha=0.8)
    ax.add_patch(rect)
    
    # Layer name
    ax.text(5, y + layer_height * 0.65, f'Layer {layer_num}: {layer_name}', 
            fontsize=16, weight='bold', ha='center', va='center')
    
    # Protocols
    ax.text(5, y + layer_height * 0.25, protocols, 
            fontsize=11, ha='center', va='center', style='italic')

# Add arrows between layers
for i in range(3):
    y1 = y_start - i * (layer_height + layer_spacing)
    y2 = y1 - layer_height - layer_spacing
    
    # Downward arrow (sending data)
    ax.annotate('', xy=(9.5, y2 + layer_height), xytext=(9.5, y1),
                arrowprops=dict(arrowstyle='->', lw=2.5, color='darkgreen'))
    
    # Upward arrow (receiving data)
    ax.annotate('', xy=(0.5, y1), xytext=(0.5, y2 + layer_height),
                arrowprops=dict(arrowstyle='->', lw=2.5, color='darkblue'))

# Labels for arrows
ax.text(9.8, 7, 'Sending\nData\n(Encapsulation)', fontsize=11, 
        ha='left', va='center', color='darkgreen', weight='bold')
ax.text(0.2, 7, 'Receiving\nData\n(Decapsulation)', fontsize=11, 
        ha='right', va='center', color='darkblue', weight='bold')

# Add note at bottom
note_text = "Each layer adds its own header to the data\nfrom the layer above, creating a protocol stack"
ax.text(5, 1.5, note_text, fontsize=12, ha='center', va='center',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8, edgecolor='black', linewidth=2))

plt.tight_layout()
plt.savefig('tcpip-stack.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Generated tcpip-stack.png")
