#!/usr/bin/env python3
"""
Generate architecture diagram for 6-Agent System
Shows the complete flow and relationships between all agents
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# Create figure and axis
fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Define colors for each agent
colors = {
    'orchestrator': '#FF6B6B',  # Red
    'planner': '#4ECDC4',       # Teal
    'coder': '#45B7D1',         # Blue
    'critic': '#F7DC6F',        # Yellow
    'file_manager': '#BB8FCE',  # Purple
    'qa_validator': '#52BE80'   # Green
}

# Agent positions
positions = {
    'orchestrator': (5, 8.5),
    'planner': (2, 6),
    'coder': (4, 6),
    'critic': (6, 6),
    'file_manager': (8, 6),
    'qa_validator': (5, 3.5)
}

# Draw agents
agents = {}
for agent, (x, y) in positions.items():
    if agent == 'orchestrator':
        # Larger box for orchestrator
        box = FancyBboxPatch((x-1.2, y-0.4), 2.4, 0.8,
                           boxstyle="round,pad=0.1",
                           facecolor=colors[agent],
                           edgecolor='black',
                           linewidth=2)
    else:
        # Standard boxes for other agents
        box = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6,
                           boxstyle="round,pad=0.05",
                           facecolor=colors[agent],
                           edgecolor='black',
                           linewidth=1.5)
    ax.add_patch(box)
    agents[agent] = box

# Add agent labels
labels = {
    'orchestrator': 'WORKFLOW\nORCHESTRATOR\n(Agent 1)',
    'planner': 'PROJECT\nPLANNER\n(Agent 2)',
    'coder': 'CODE\nGENERATOR\n(Agent 3)',
    'critic': 'CODE\nCRITIC\n(Agent 4)',
    'file_manager': 'FILE\nMANAGER\n(Agent 5)',
    'qa_validator': 'QA\nVALIDATOR\n(Agent 6)'
}

for agent, (x, y) in positions.items():
    if agent == 'orchestrator':
        ax.text(x, y, labels[agent], ha='center', va='center', 
                fontsize=10, fontweight='bold', color='white')
    else:
        ax.text(x, y, labels[agent], ha='center', va='center', 
                fontsize=8, fontweight='bold')

# Draw connections from orchestrator to all agents
for agent in ['planner', 'coder', 'critic', 'file_manager']:
    x1, y1 = positions['orchestrator']
    x2, y2 = positions[agent]
    ax.arrow(x1, y1-0.4, x2-x1, y2-y1+0.7, 
             head_width=0.15, head_length=0.1, 
             fc='gray', ec='gray', alpha=0.7)

# Draw connections from all agents to QA validator
for agent in ['planner', 'coder', 'critic', 'file_manager']:
    x1, y1 = positions[agent]
    x2, y2 = positions['qa_validator']
    ax.arrow(x1, y1-0.3, x2-x1, y2-y1+0.6, 
             head_width=0.15, head_length=0.1, 
             fc='darkgray', ec='darkgray', alpha=0.6)

# Add workflow steps
steps = [
    (1, 7.5, "1. Receive Request"),
    (1, 5, "2. Plan Architecture"),
    (3, 5, "3. Generate Code"),
    (5, 5, "4. Review Quality"),
    (7, 5, "5. Organize Files"),
    (5, 2.5, "6. Validate & Test"),
    (9, 2, "7. Return Project")
]

for step, x, text in steps:
    ax.text(x, 9.5-step*0.3, text, ha='left', va='center',
            fontsize=9, style='italic', color='#2C3E50')

# Add title
ax.text(5, 9.5, '6-AGENT CODE GENERATION SYSTEM', 
        ha='center', va='center', fontsize=16, fontweight='bold')

# Add capabilities for each agent
capabilities = {
    'planner': ['• Requirement Analysis', '• Tech Selection', '• Architecture Design'],
    'coder': ['• Code Generation', '• Framework Support', '• Business Logic'],
    'critic': ['• Code Review', '• Best Practices', '• Optimization'],
    'file_manager': ['• File Structure', '• Dependencies', '• Deployment Config'],
    'qa_validator': ['• Testing', '• Security Scan', '• Quality Score']
}

# Add capability boxes
for agent, caps in capabilities.items():
    x, y = positions[agent]
    y_offset = -0.8
    for i, cap in enumerate(caps):
        ax.text(x, y + y_offset - i*0.2, cap, ha='center', va='center',
                fontsize=7, color='#34495E')

# Add input/output boxes
# Input
input_box = FancyBboxPatch((0.5, 8.2), 1.5, 0.6,
                         boxstyle="round,pad=0.05",
                         facecolor='#E8F5E9',
                         edgecolor='#4CAF50',
                         linewidth=1.5)
ax.add_patch(input_box)
ax.text(1.25, 8.5, 'USER\nREQUEST', ha='center', va='center', 
        fontsize=9, fontweight='bold', color='#2E7D32')

# Output
output_box = FancyBboxPatch((8, 3.2), 1.5, 0.6,
                          boxstyle="round,pad=0.05",
                          facecolor='#E3F2FD',
                          edgecolor='#2196F3',
                          linewidth=1.5)
ax.add_patch(output_box)
ax.text(8.75, 3.5, 'VALIDATED\nPROJECT', ha='center', va='center', 
        fontsize=9, fontweight='bold', color='#1565C0')

# Draw arrows for input/output
ax.arrow(2, 8.5, 1.8, 0, head_width=0.15, head_length=0.1, 
         fc='#4CAF50', ec='#4CAF50')
ax.arrow(6.2, 3.5, 1.8, 0, head_width=0.15, head_length=0.1, 
         fc='#2196F3', ec='#2196F3')

# Add legend for agent types
legend_elements = [
    mpatches.Rectangle((0, 0), 1, 1, fc=colors['orchestrator'], label='Orchestrator'),
    mpatches.Rectangle((0, 0), 1, 1, fc=colors['planner'], label='Planner'),
    mpatches.Rectangle((0, 0), 1, 1, fc=colors['coder'], label='Coder'),
    mpatches.Rectangle((0, 0), 1, 1, fc=colors['critic'], label='Critic'),
    mpatches.Rectangle((0, 0), 1, 1, fc=colors['file_manager'], label='File Manager'),
    mpatches.Rectangle((0, 0), 1, 1, fc=colors['qa_validator'], label='QA Validator')
]
ax.legend(handles=legend_elements, loc='lower center', ncol=6, 
          frameon=True, fancybox=True, shadow=True)

# Add metrics box
metrics_box = FancyBboxPatch((0.2, 0.5), 3, 1.5,
                           boxstyle="round,pad=0.05",
                           facecolor='#F5F5F5',
                           edgecolor='black',
                           linewidth=1)
ax.add_patch(metrics_box)

metrics_text = """SYSTEM METRICS
• Total Agents: 6
• API Endpoints: 11
• Frameworks: 5
• Avg. Time: 400s
• Quality Target: 85%"""

ax.text(1.7, 1.25, metrics_text, ha='center', va='center',
        fontsize=8, fontfamily='monospace')

# Save the diagram
plt.tight_layout()
plt.savefig('6-agent-system-architecture.png', dpi=300, bbox_inches='tight')
plt.savefig('6-agent-system-architecture.pdf', format='pdf', bbox_inches='tight')

print("✅ Architecture diagram saved as:")
print("   - 6-agent-system-architecture.png")
print("   - 6-agent-system-architecture.pdf")