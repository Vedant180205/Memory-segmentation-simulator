import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
from datetime import datetime
from models import Process, Segment
from memory_manager import MemoryManager

class SegmentationSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#1e1e2e")
        
        # Data
        self.processes = []
        self.current_process_index = 0
        self.total_memory = 4096
        self.mem_manager = MemoryManager(self.total_memory)
        self.allocation_strategy = "first"
        self.trace_mode = False
        
        # Setup styles (light text on dark background)
        self.setup_styles()
        self.setup_ui()
        self.new_process()
        self.update_all()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Base colors
        bg = "#1e1e2e"          # dark background
        fg = "#ffffff"          # white text
        selectbg = "#3b82f6"    # blue selection
        entrybg = "#2d2d3d"     # slightly lighter for entries
        buttonbg = "#3b82f6"
        buttonfg = "#ffffff"
        
        # Configure common styles
        style.configure(".", background=bg, foreground=fg, fieldbackground=entrybg)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TLabelframe.Label", background=bg, foreground=fg, font=("Segoe UI", 10, "bold"))
        
        # Buttons
        style.configure("TButton", background=buttonbg, foreground=buttonfg, 
                       borderwidth=0, focusthickness=0, padding=6, font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#2563eb")])
        
        # Entry
        style.configure("TEntry", fieldbackground=entrybg, foreground=fg, insertcolor=fg,
                       borderwidth=1, relief="solid")
        
        # Combobox
        style.configure("TCombobox", fieldbackground=entrybg, foreground=fg, 
                       selectbackground=selectbg, selectforeground=fg)
        style.map("TCombobox", fieldbackground=[("readonly", entrybg)])
        
        # Scrollbar
        style.configure("Vertical.TScrollbar", background=entrybg, troughcolor=bg,
                       arrowcolor=fg, borderwidth=0)
        
        # Treeview (segment table)
        style.configure("Treeview", background=entrybg, foreground=fg, 
                       fieldbackground=entrybg, borderwidth=0)
        style.map("Treeview", background=[("selected", selectbg)])
        style.configure("Treeview.Heading", background=bg, foreground=fg,
                       font=("Segoe UI", 10, "bold"), relief="flat")
        
        # Progressbar
        style.configure("TProgressbar", background="#22c55e", troughcolor=entrybg)
        
        # Radiobutton
        style.configure("TRadiobutton", background=bg, foreground=fg, 
                       selectcolor=bg, focusthickness=0)
        
        # Checkbutton
        style.configure("TCheckbutton", background=bg, foreground=fg,
                       selectcolor=bg, focusthickness=0)
    
    def setup_ui(self):
        # Main container with paned window
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#1e1e2e", 
                                    sashrelief=tk.RAISED, sashwidth=8)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel (segment management)
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, width=450)
        
        # Right panel (visualization & translation)
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, width=800)
        
        # ========== LEFT PANEL CONTENT ==========
        # Process selector
        proc_frame = ttk.LabelFrame(left_frame, text="Process Management", padding=10)
        proc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(proc_frame, text="Current Process:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.process_combo = ttk.Combobox(proc_frame, state="readonly", width=25)
        self.process_combo.grid(row=0, column=1, padx=5, pady=5)
        self.process_combo.bind("<<ComboboxSelected>>", self.on_process_change)
        
        ttk.Button(proc_frame, text="➕ New Process", command=self.new_process).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(proc_frame, text="❌ Delete Process", command=self.delete_process).grid(row=0, column=3, padx=5, pady=5)
        
        # Segment table
        table_frame = ttk.LabelFrame(left_frame, text="Segment Table", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("Name", "Size", "Base", "Perms")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90)
        self.tree.column("Name", width=120)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Segment buttons
        seg_btn_frame = ttk.Frame(left_frame)
        seg_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(seg_btn_frame, text="➕ Add Segment", command=self.add_segment_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(seg_btn_frame, text="✏️ Edit Segment", command=self.edit_segment_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(seg_btn_frame, text="🗑️ Delete Segment", command=self.delete_segment).pack(side=tk.LEFT, padx=5)
        
        # Allocation strategy
        strat_frame = ttk.LabelFrame(left_frame, text="Allocation Strategy", padding=10)
        strat_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.strategy_var = tk.StringVar(value="first")
        strategies = [("First Fit", "first"), ("Best Fit", "best"), ("Worst Fit", "worst")]
        for i, (text, val) in enumerate(strategies):
            rb = ttk.Radiobutton(strat_frame, text=text, variable=self.strategy_var, value=val,
                                 command=self.change_strategy)
            rb.grid(row=0, column=i, padx=10, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(left_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="🎯 Assign Bases", command=self.assign_bases).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🔄 Compaction", command=self.compact_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="💾 Save", command=self.save_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📂 Load", command=self.load_all).pack(side=tk.LEFT, padx=5)
        
        # ========== RIGHT PANEL CONTENT ==========
        # Memory gauge
        gauge_frame = ttk.LabelFrame(right_frame, text="Memory Status", padding=10)
        gauge_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.usage_label = ttk.Label(gauge_frame, text="📊 Memory Usage: 0%")
        self.usage_label.pack(side=tk.LEFT, padx=5)
        
        self.frag_label = ttk.Label(gauge_frame, text="🧩 Fragmentation: 0%")
        self.frag_label.pack(side=tk.RIGHT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(gauge_frame, mode='determinate', length=400)
        self.progress.pack(fill=tk.X, pady=5)
        
        # Matplotlib figure (colors adjusted for dark theme)
        self.fig, self.ax = plt.subplots(figsize=(10, 3), facecolor="#1e1e2e")
        self.ax.set_facecolor("#1e1e2e")
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.title.set_color('#22c55e')
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Translation panel
        trans_frame = ttk.LabelFrame(right_frame, text="Address Translation", padding=10)
        trans_frame.pack(fill=tk.X, padx=10, pady=10)
        
        input_frame = ttk.Frame(trans_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Segment Index:").pack(side=tk.LEFT, padx=5)
        self.entry_seg = ttk.Entry(input_frame, width=8)
        self.entry_seg.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(input_frame, text="Offset:").pack(side=tk.LEFT, padx=5)
        self.entry_off = ttk.Entry(input_frame, width=10)
        self.entry_off.pack(side=tk.LEFT, padx=5)
        
        self.translate_btn = ttk.Button(input_frame, text="Translate", command=self.translate_address)
        self.translate_btn.pack(side=tk.LEFT, padx=10)
        
        self.trace_var = tk.BooleanVar(value=False)
        trace_check = ttk.Checkbutton(trans_frame, text="🐾 Step-by-Step Trace", variable=self.trace_var,
                                      command=self.toggle_trace)
        trace_check.pack(anchor=tk.W, pady=5)
        
        self.result_label = ttk.Label(trans_frame, text="", font=("Segoe UI", 12, "bold"))
        self.result_label.pack(anchor=tk.W, pady=5)
        
        # Trace text area (using tk.Text for better control)
        self.trace_text = tk.Text(trans_frame, height=6, bg="#2d2d3d", fg="#ffffff", 
                                  wrap=tk.WORD, insertbackground="white")
        self.trace_text.pack(fill=tk.X, pady=5)
    
    # ------------------- All methods remain exactly as before -------------------
    # (They are unchanged from the previous working version)
    # I will include them for completeness, but they are identical to the earlier correct methods.
    
    def change_strategy(self):
        self.allocation_strategy = self.strategy_var.get()
    
    def get_current_process(self):
        if 0 <= self.current_process_index < len(self.processes):
            return self.processes[self.current_process_index]
        return None
    
    def refresh_process_combo(self):
        names = [f"{p.name} (PID {p.pid})" for p in self.processes]
        self.process_combo['values'] = names
        if names:
            self.process_combo.set(names[self.current_process_index])
        self.refresh_segment_table()
    
    def refresh_segment_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        proc = self.get_current_process()
        if proc:
            for seg in proc.segments:
                self.tree.insert("", tk.END, values=(seg.name, seg.size, seg.base, seg.permissions))
    
    def on_process_change(self, event=None):
        choice = self.process_combo.get()
        for idx, p in enumerate(self.processes):
            if f"{p.name} (PID {p.pid})" == choice:
                self.current_process_index = idx
                break
        self.refresh_segment_table()
        self.update_memory_plot()
        self.update_stats()
    
    def new_process(self):
        name = simpledialog.askstring("New Process", "Enter process name:", parent=self.root)
        if not name:
            name = f"Process{len(self.processes)+1}"
        pid = len(self.processes) + 1
        proc = Process(pid, name)
        self.processes.append(proc)
        self.current_process_index = len(self.processes) - 1
        self.refresh_process_combo()
        self.update_memory_plot()
        self.update_stats()
    
    def delete_process(self):
        if len(self.processes) <= 1:
            messagebox.showerror("Error", "At least one process required")
            return
        del self.processes[self.current_process_index]
        if self.current_process_index >= len(self.processes):
            self.current_process_index = len(self.processes) - 1
        self.refresh_process_combo()
        self.update_memory_plot()
        self.update_stats()
    
    def add_segment_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Segment")
        dialog.geometry("350x300")
        dialog.configure(bg="#1e1e2e")
        dialog.grab_set()
        
        # Use tk widgets with explicit colors
        tk.Label(dialog, text="Segment Name:", bg="#1e1e2e", fg="#ffffff").pack(pady=5)
        name_entry = tk.Entry(dialog, bg="#2d2d3d", fg="#ffffff", insertbackground="white")
        name_entry.pack()
        
        tk.Label(dialog, text="Size (bytes):", bg="#1e1e2e", fg="#ffffff").pack(pady=5)
        size_entry = tk.Entry(dialog, bg="#2d2d3d", fg="#ffffff", insertbackground="white")
        size_entry.pack()
        
        tk.Label(dialog, text="Permissions (r/w/x):", bg="#1e1e2e", fg="#ffffff").pack(pady=5)
        perm_entry = tk.Entry(dialog, bg="#2d2d3d", fg="#ffffff", insertbackground="white")
        perm_entry.insert(0, "rwx")
        perm_entry.pack()
        
        def add():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Name required")
                return
            try:
                size = int(size_entry.get())
                if size <= 0: raise ValueError
            except:
                messagebox.showerror("Error", "Invalid size")
                return
            perms = perm_entry.get().strip()
            if not all(c in "rwx" for c in perms):
                messagebox.showerror("Error", "Permissions must be r,w,x only")
                return
            proc = self.get_current_process()
            proc.segments.append(Segment(name, size, perms))
            self.refresh_segment_table()
            self.update_memory_plot()
            self.update_stats()
            dialog.destroy()
        
        tk.Button(dialog, text="Add Segment", command=add, bg="#10b981", fg="#ffffff", 
                 activebackground="#059669", activeforeground="white").pack(pady=20)
    
    def edit_segment_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a segment first")
            return
        idx = self.tree.index(selected[0])
        proc = self.get_current_process()
        seg = proc.segments[idx]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Segment")
        dialog.geometry("350x300")
        dialog.configure(bg="#1e1e2e")
        dialog.grab_set()
        
        tk.Label(dialog, text="Name:", bg="#1e1e2e", fg="#ffffff").pack(pady=5)
        name_entry = tk.Entry(dialog, bg="#2d2d3d", fg="#ffffff", insertbackground="white")
        name_entry.insert(0, seg.name)
        name_entry.pack()
        
        tk.Label(dialog, text="Size:", bg="#1e1e2e", fg="#ffffff").pack(pady=5)
        size_entry = tk.Entry(dialog, bg="#2d2d3d", fg="#ffffff", insertbackground="white")
        size_entry.insert(0, str(seg.size))
        size_entry.pack()
        
        tk.Label(dialog, text="Permissions:", bg="#1e1e2e", fg="#ffffff").pack(pady=5)
        perm_entry = tk.Entry(dialog, bg="#2d2d3d", fg="#ffffff", insertbackground="white")
        perm_entry.insert(0, seg.permissions)
        perm_entry.pack()
        
        def save():
            seg.name = name_entry.get().strip()
            try:
                seg.size = int(size_entry.get())
            except:
                messagebox.showerror("Error", "Invalid size")
                return
            seg.permissions = perm_entry.get().strip()
            self.refresh_segment_table()
            self.update_memory_plot()
            self.update_stats()
            dialog.destroy()
        
        tk.Button(dialog, text="Save", command=save, bg="#f59e0b", fg="#ffffff",
                 activebackground="#d97706").pack(pady=20)
    
    def delete_segment(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        proc = self.get_current_process()
        del proc.segments[idx]
        self.refresh_segment_table()
        self.update_memory_plot()
        self.update_stats()
    
    def assign_bases(self):
        proc = self.get_current_process()
        if not proc.segments:
            messagebox.showinfo("Info", "No segments to assign")
            return
        success = self.mem_manager.assign_bases(proc.segments, self.allocation_strategy)
        if success:
            self.refresh_segment_table()
            self.update_memory_plot()
            self.update_stats()
            messagebox.showinfo("Success", f"Bases assigned using {self.allocation_strategy} fit")
        else:
            messagebox.showerror("Error", "Not enough contiguous memory!")
    
    def compact_memory(self):
        proc = self.get_current_process()
        if not proc.segments:
            return
        self.mem_manager.compact(proc.segments)
        self.refresh_segment_table()
        self.update_memory_plot()
        self.update_stats()
        messagebox.showinfo("Compaction", "Memory compacted!")
    
    def update_stats(self):
        proc = self.get_current_process()
        if not proc:
            used = 0
            free = self.total_memory
            frag = 0
        else:
            used = proc.total_memory()
            free = self.total_memory - used
            if free > 0:
                largest_hole = max((size for _, size in self.mem_manager.free_holes), default=0)
                frag = (1 - largest_hole / free) * 100 if free > 0 else 0
            else:
                frag = 0
        used_percent = (used / self.total_memory) * 100
        self.progress['value'] = used_percent
        self.usage_label.config(text=f"📊 Memory Usage: {used}/{self.total_memory} bytes ({used_percent:.1f}%)")
        self.frag_label.config(text=f"🧩 Fragmentation: {frag:.1f}%")
    
    def update_memory_plot(self):
        proc = self.get_current_process()
        self.ax.clear()
        self.ax.set_facecolor("#1e1e2e")
        self.ax.set_ylim(-0.5, 1.5)
        self.ax.set_xlim(0, self.total_memory)
        self.ax.set_yticks([])
        self.ax.set_xlabel("Physical Address Space", fontsize=12, color="white")
        self.ax.set_title(f"🧠 Memory Map — {proc.name if proc else 'No Process'}", fontsize=14, fontweight="bold", color="#22c55e")
        self.ax.tick_params(axis='x', colors='white')
        
        if proc:
            # Draw free holes
            for start, size in self.mem_manager.free_holes:
                if size > 0:
                    self.ax.barh(0.5, size, left=start, height=0.4, color="#475569", alpha=0.3, edgecolor='none')
            
            # Draw segments
            colors = ["#3b82f6", "#f59e0b", "#10b981", "#ec489a", "#8b5cf6", "#06b6d4"]
            for i, seg in enumerate(proc.segments):
                color = colors[i % len(colors)]
                self.ax.barh(0.5, seg.size, left=seg.base, height=0.4, color=color,
                             edgecolor="white", linewidth=2, alpha=0.9)
                self.ax.text(seg.base + seg.size/2, 0.5, f"{seg.name}\n[{seg.base}-{seg.base+seg.size}]",
                             ha='center', va='center', fontsize=9, fontweight='bold', color="white")
        
        # Draw pointer if translation valid
        try:
            seg_idx = int(self.entry_seg.get())
            offset = int(self.entry_off.get())
            proc = self.get_current_process()
            if proc and 0 <= seg_idx < len(proc.segments) and offset < proc.segments[seg_idx].size:
                pa = proc.segments[seg_idx].base + offset
                self.ax.axvline(pa, color="#facc15", linewidth=3, linestyle='--', alpha=0.8)
                self.ax.text(pa, 1.1, f"🔴 PA={pa}", ha='center', fontsize=10,
                             bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.2', edgecolor='none'))
        except:
            pass
        
        self.ax.grid(axis='x', linestyle=':', alpha=0.3, color='gray')
        self.fig.tight_layout()
        self.canvas.draw()
    
    def translate_address(self):
        proc = self.get_current_process()
        if not proc:
            self.result_label.config(text="No process selected")
            return
        try:
            seg_idx = int(self.entry_seg.get())
            offset = int(self.entry_off.get())
        except:
            self.result_label.config(text="Invalid input")
            return
        
        if seg_idx < 0 or seg_idx >= len(proc.segments):
            self.result_label.config(text="Segment index out of range")
            return
        
        seg = proc.segments[seg_idx]
        self.trace_text.delete("1.0", tk.END)
        
        if self.trace_var.get():
            trace = f"Step 1: Segment {seg_idx} → {seg.name}, Base={seg.base}, Limit={seg.size}\n"
            trace += f"Step 2: Check offset {offset} < {seg.size} → {offset < seg.size}\n"
            if offset >= seg.size:
                trace += "Step 3: OFFSET EXCEEDS LIMIT → SEGMENTATION FAULT!\n"
                self.trace_text.insert("1.0", trace)
                self.result_label.config(text="Segmentation Fault!")
                self.update_memory_plot()
                return
            physical = seg.base + offset
            trace += f"Step 3: Physical Address = {seg.base} + {offset} = {physical}\n"
            trace += "Translation successful."
            self.trace_text.insert("1.0", trace)
            self.result_label.config(text=f"Physical Address = {physical}")
        else:
            if offset >= seg.size:
                self.result_label.config(text="Segmentation Fault!")
            else:
                physical = seg.base + offset
                self.result_label.config(text=f"Physical Address = {physical}")
        self.update_memory_plot()
    
    def toggle_trace(self):
        self.trace_mode = self.trace_var.get()
    
    def update_all(self):
        self.refresh_segment_table()
        self.update_memory_plot()
        self.update_stats()
    
    def save_all(self):
        if not os.path.exists("data"):
            os.mkdir("data")
        filename = f"data/segments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = []
        for p in self.processes:
            data.append({
                "pid": p.pid,
                "name": p.name,
                "segments": [{"name": s.name, "size": s.size, "permissions": s.permissions, "base": s.base} for s in p.segments]
            })
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Saved", f"Saved to {filename}")
    
    def load_all(self):
        filename = filedialog.askopenfilename(initialdir="data", title="Load Processes",
                                              filetypes=[("JSON files", "*.json")])
        if not filename:
            return
        with open(filename, "r") as f:
            data = json.load(f)
        self.processes = []
        for proc_data in data:
            p = Process(proc_data["pid"], proc_data["name"])
            for seg_data in proc_data["segments"]:
                p.segments.append(Segment(seg_data["name"], seg_data["size"], seg_data["permissions"], seg_data["base"]))
            self.processes.append(p)
        if self.processes:
            self.current_process_index = 0
            self.refresh_process_combo()
            self.mem_manager.reset_holes(self.get_current_process().segments)
            self.update_all()
            messagebox.showinfo("Loaded", f"Loaded {len(self.processes)} processes")