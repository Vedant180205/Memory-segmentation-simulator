import json
from typing import List, Dict, Optional

class Segment:
    """Represents a single segment."""
    def __init__(self, name: str, size: int, permissions: str = "rwx", base: int = 0):
        self.name = name          # e.g., "Code", "Data"
        self.size = size          # limit
        self.permissions = permissions  # 'r', 'w', 'x' combination
        self.base = base

    def to_dict(self):
        return {"name": self.name, "size": self.size, "permissions": self.permissions, "base": self.base}

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["size"], data["permissions"], data["base"])

class Process:
    """Each process has its own segment table."""
    def __init__(self, pid: int, name: str = ""):
        self.pid = pid
        self.name = name or f"Process {pid}"
        self.segments: List[Segment] = []

    def add_segment(self, segment: Segment):
        self.segments.append(segment)

    def remove_segment(self, index: int):
        if 0 <= index < len(self.segments):
            del self.segments[index]

    def total_memory(self) -> int:
        return sum(seg.size for seg in self.segments)

    def to_dict(self):
        return {
            "pid": self.pid,
            "name": self.name,
            "segments": [seg.to_dict() for seg in self.segments]
        }

    @classmethod
    def from_dict(cls, data):
        proc = cls(data["pid"], data["name"])
        proc.segments = [Segment.from_dict(s) for s in data["segments"]]
        return proc