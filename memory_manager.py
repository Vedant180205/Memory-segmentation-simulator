from typing import List, Tuple, Optional
from models import Process, Segment

class MemoryManager:
    """Handles base address assignment, free holes, allocation strategies."""
    def __init__(self, total_physical_memory: int):
        self.total_memory = total_physical_memory
        self.free_holes: List[Tuple[int, int]] = []  # list of (start, size) free blocks

    def reset_holes(self, segments: List[Segment]):
        """Rebuild free list after segment changes."""
        if not segments:
            self.free_holes = [(0, self.total_memory)]
            return

        # Sort segments by base
        sorted_segs = sorted(segments, key=lambda s: s.base)
        holes = []
        prev_end = 0
        for seg in sorted_segs:
            if seg.base > prev_end:
                holes.append((prev_end, seg.base - prev_end))
            prev_end = seg.base + seg.size
        if prev_end < self.total_memory:
            holes.append((prev_end, self.total_memory - prev_end))
        self.free_holes = holes

    def assign_bases(self, segments: List[Segment], strategy: str = "first") -> bool:
        """Assign bases using chosen strategy. Returns success."""
        # Sort segments by size for best/worst fit (largest first for worst fit)
        segs_to_assign = list(segments)
        if strategy == "best":
            segs_to_assign.sort(key=lambda s: s.size)
        elif strategy == "worst":
            segs_to_assign.sort(key=lambda s: -s.size)
        else:  # first or next (we'll do first for simplicity)
            segs_to_assign = segments[:]

        # We'll reset holes after clearing all bases, then allocate one by one
        for seg in segs_to_assign:
            seg.base = -1  # mark unassigned

        # Simulate allocation
        temp_holes = [(0, self.total_memory)]
        for seg in segs_to_assign:
            allocated = False
            for i, (start, size) in enumerate(temp_holes):
                if size >= seg.size:
                    seg.base = start
                    # Update hole list
                    if size == seg.size:
                        temp_holes.pop(i)
                    else:
                        temp_holes[i] = (start + seg.size, size - seg.size)
                    allocated = True
                    break
            if not allocated:
                return False  # not enough memory

        # If success, apply bases to original segments (preserve order)
        # We need to map back to original order
        base_map = {seg: seg.base for seg in segs_to_assign}
        for seg in segments:
            seg.base = base_map[seg]

        # Update free holes
        self.reset_holes(segments)
        return True

    def compact(self, segments: List[Segment]):
        """Move all segments together starting at 0."""
        current = 0
        for seg in segments:
            seg.base = current
            current += seg.size
        self.reset_holes(segments)