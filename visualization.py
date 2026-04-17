import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Optional
from models import Segment, Process

def visualize_memory(process: Process, highlight_seg_index: Optional[int] = None,
                     pointer_address: Optional[int] = None, free_holes: List = None):
    """Draw memory map with segments and holes."""
    if not process.segments and not free_holes:
        return

    fig, ax = plt.subplots(figsize=(12, 3))

    # Draw free holes first (background)
    if free_holes:
        for start, size in free_holes:
            if size > 0:
                ax.barh(0.1, size, left=start, height=0.4, color="#cbd5e1",
                        edgecolor="white", linewidth=1, label="Free" if start==free_holes[0][0] else "")

    # Draw segments
    colors = ["#3b82f6", "#f59e0b", "#10b981", "#6366f1", "#ec489a", "#8b5cf6"]
    for i, seg in enumerate(process.segments):
        color = colors[i % len(colors)]
        if i == highlight_seg_index:
            color = "#ef4444"  # red highlight
        ax.barh(0.1, seg.size, left=seg.base, height=0.4, color=color,
                edgecolor="white", linewidth=2)
        # Label
        label = f"{seg.name}\n[{seg.base}-{seg.base+seg.size}]"
        ax.text(seg.base + seg.size/2, 0.1, label, ha='center', va='center',
                fontsize=9, fontweight='bold', color="white")

    # Draw pointer if given
    if pointer_address is not None:
        ax.axvline(pointer_address, color='black', linewidth=2, linestyle='--')
        ax.text(pointer_address, 0.5, f"PA = {pointer_address}", ha='center',
                fontsize=10, bbox=dict(facecolor='yellow', alpha=0.7))

    ax.set_xlim(0, max(process.total_memory(), 100))
    ax.set_ylim(-0.2, 0.5)
    ax.set_yticks([])
    ax.set_xlabel("Physical Memory Address")
    ax.set_title(f"Memory Layout - {process.name}")
    ax.grid(axis='x', linestyle=':', alpha=0.3)
    plt.tight_layout()
    plt.show()