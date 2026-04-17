import json
from models import Process

def save_processes(processes, filename):
    data = [p.to_dict() for p in processes]
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def load_processes(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return [Process.from_dict(d) for d in data]