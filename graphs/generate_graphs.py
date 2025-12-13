#!/usr/bin/env python3
"""
Generate graphs and visualizations for the FIEK AI Chatbot project results.
Run this script to generate all visualization images for the README.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']

# Create output directory
output_dir = Path('graphs')
output_dir.mkdir(exist_ok=True)

# 1. Document Type Distribution (Pie Chart)
fig, ax = plt.subplots(figsize=(8, 8))
labels = ['Web Pages', 'PDF Documents']
sizes = [19, 7]
colors_pie = ['#2E86AB', '#A23B72']
explode = (0.05, 0)

ax.pie(sizes, explode=explode, labels=labels, colors=colors_pie, autopct='%1.1f%%',
       shadow=True, startangle=90, textprops={'fontsize': 12, 'weight': 'bold'})
ax.set_title('Document Type Distribution\n(Total: 26 documents)', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(output_dir / 'document_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Content Distribution (Bar Chart)
fig, ax = plt.subplots(figsize=(10, 6))
categories = ['Academic\nPrograms', 'Staff\nInformation', 'Regulations', 'Schedules', 'Other']
percentages = [35, 25, 20, 10, 10]
bars = ax.bar(categories, percentages, color=colors[:5], edgecolor='black', linewidth=1.5)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
ax.set_title('Knowledge Base Content Distribution', fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(0, 40)
ax.grid(axis='y', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig(output_dir / 'content_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Response Time Distribution (Bar Chart)
fig, ax = plt.subplots(figsize=(10, 6))
time_ranges = ['< 0.5s', '0.5-1s', '1-2s', '> 2s']
percentages = [20, 50, 25, 5]
bars = ax.bar(time_ranges, percentages, color=['#6A994E', '#2E86AB', '#F18F01', '#C73E1D'], 
              edgecolor='black', linewidth=1.5)

# Add value labels
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_ylabel('Percentage of Queries (%)', fontsize=12, fontweight='bold')
ax.set_xlabel('Response Time', fontsize=12, fontweight='bold')
ax.set_title('Response Time Distribution', fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(0, 60)
ax.grid(axis='y', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig(output_dir / 'response_time.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. System Performance Metrics (Horizontal Bar Chart)
fig, ax = plt.subplots(figsize=(10, 6))
metrics = ['Precision@5', 'Language\nAccuracy', 'Response\nQuality']
values = [80, 90, 85]  # Using numeric values for visualization
colors_metrics = ['#2E86AB', '#6A994E', '#F18F01']
bars = ax.barh(metrics, values, color=colors_metrics, edgecolor='black', linewidth=1.5)

# Add value labels
for i, bar in enumerate(bars):
    width = bar.get_width()
    label = f'{int(width)}%' if i < 2 else 'High'
    ax.text(width + 2, bar.get_y() + bar.get_height()/2.,
            label,
            ha='left', va='center', fontsize=11, fontweight='bold')

ax.set_xlabel('Performance Score (%)', fontsize=12, fontweight='bold')
ax.set_title('System Performance Metrics', fontsize=14, fontweight='bold', pad=20)
ax.set_xlim(0, 100)
ax.grid(axis='x', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig(output_dir / 'performance_metrics.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Dataset Statistics (Multi-bar Chart)
fig, ax = plt.subplots(figsize=(10, 6))
categories = ['Total\nDocuments', 'Total\nCharacters', 'Avg Chars\nper Document', 'Vector\nEmbeddings']
values = [26, 88.187, 3.391, 994]  # Normalized for visualization
# Normalize large values for better visualization
normalized_values = [26, 88.187/10, 3.391, 994/40]  # Scale down for visualization
bars = ax.bar(categories, normalized_values, color=colors[:4], edgecolor='black', linewidth=1.5)

# Add actual value labels
labels = ['26', '88,187', '3,391', '994']
for i, (bar, label) in enumerate(zip(bars, labels)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            label,
            ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_ylabel('Normalized Value', fontsize=12, fontweight='bold')
ax.set_title('Dataset Statistics Overview', fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='y', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig(output_dir / 'dataset_stats.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. Processing Pipeline Flow (Simplified)
fig, ax = plt.subplots(figsize=(12, 4))
stages = ['Data\nCollection', 'Preprocessing\n& Chunking', 'Embedding\nGeneration', 'Vector\nIndexing', 'Query\nProcessing', 'Response\nGeneration']
y_pos = [0.5] * len(stages)
x_pos = np.arange(len(stages))

# Draw flow
for i in range(len(stages) - 1):
    ax.arrow(x_pos[i] + 0.4, y_pos[i], 0.2, 0, head_width=0.05, head_length=0.05, 
             fc=colors[0], ec=colors[0], linewidth=2)

# Draw boxes
for i, (x, stage) in enumerate(zip(x_pos, stages)):
    box = mpatches.FancyBboxPatch((x - 0.35, y_pos[i] - 0.15), 0.7, 0.3,
                                  boxstyle="round,pad=0.05", 
                                  facecolor=colors[i % len(colors)],
                                  edgecolor='black', linewidth=1.5)
    ax.add_patch(box)
    ax.text(x, y_pos[i], stage, ha='center', va='center', 
            fontsize=9, fontweight='bold', color='white')

ax.set_xlim(-0.5, len(stages) - 0.5)
ax.set_ylim(0, 1)
ax.axis('off')
ax.set_title('Data Processing Pipeline', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(output_dir / 'processing_pipeline.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"All graphs generated successfully in '{output_dir}' directory!")
print("Generated files:")
for file in sorted(output_dir.glob('*.png')):
    print(f"  - {file.name}")

