import tkinter as tk
from ui import SegmentationSimulatorUI

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Memory Segmentation Simulator")
    root.geometry("1300x800")
    root.configure(bg="#1e1e2e")
    app = SegmentationSimulatorUI(root)
    root.mainloop()