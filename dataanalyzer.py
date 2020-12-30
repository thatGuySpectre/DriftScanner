import tkinter as tk
import time
from tkinter import ttk, simpledialog, filedialog
import numpy as np

import pickle

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as pyplot
from datasample import DataSample
matplotlib.use("TkAgg")


class DataAnalyzer:
    def __init__(self, parent):
        self.parent_app = parent
        self.parent = parent.root
        self.window = tk.Toplevel()
        self.window.withdraw()

        self.window.title("Measurements")
        self.window.geometry("800x600")

        self.data = dict()
        self.sample_count = 0

        # Open data windows

        self.open_windows = []

        # File Menubar

        self.menubar = tk.Menu(self.window)

        self.menubar_file = tk.Menu(self.menubar, tearoff=0)
        self.menubar_file.add_command(label="Open", command=self.open_file)
        self.menubar_file.add_command(label="Save", command=self.save_file)
        self.menubar_file.add_separator()
        self.menubar_file.add_command(label="Close", command=self.close_window)

        self.menubar.add_cascade(label="File", menu=self.menubar_file)

        self.window.config(menu=self.menubar)

        # Layout
        columns = ("Title", "Brightness", "SNR", "Normalized StdDev")

        self.datasheet = ttk.Treeview(self.window, columns=columns, show="headings")

        for col in columns:
            self.datasheet.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, False))

        for h in columns:
            self.datasheet.heading(h, text=h)

        self.datasheet.pack(fill="both", expand=True, side="top")

        self.scrollbar = ttk.Scrollbar(self.datasheet)
        self.scrollbar.config(command=self.datasheet.yview)

        self.datasheet.config(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")

        # Buttons to get detailed info: (function_name, "Button Title")
        self.functions = ((self.f_show_crossection, "Show Crosssection"),
                          (self.f_show_flattened_line, "t-S-Graph"),
                          (self.f_rename_sample, "Rename Sample"),
                          (self.f_delete_selected, "Delete Selected"),
                          (self.f_delete_all, "Delete All"),
                          (self.f_open, "Open Measurements"),
                          (self.f_save_selected, "Save Measurements"))

        for func in self.functions:
            b = tk.Button(master=self.window, command=func[0], text=func[1])
            b.pack(side=tk.LEFT)


        # Event handling

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)


    def open_file(self):
        pass

    def save_file(self):
        pass

    def close_window(self):
        self.window.withdraw()

    def add_sample(self, sample, title=""):
        if not title:
            self.sample_count += 1
            title = f"Measurement {self.sample_count}"
        key = self.datasheet.insert("", "end", values=(title, *self.get_sample_values(sample)))
        self.data[key] = sample

    def get_sample_values(self, sample):
        return sample.signal, sample.snr, np.std(sample.get_flattened_line() / np.mean(sample.get_flattened_line()))

    def f_show_crossection(self):
        samples = [self.data[iid] for iid in self.datasheet.selection()]
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self.window, samples, "Show Crosssection", title))

    def f_show_flattened_line(self):
        samples = [self.data[iid] for iid in self.datasheet.selection()]
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self.window, samples, "t-S-Graph", title))

    def f_show_SNR_StdDev_graph(self):
        samples = [self.data[iid] for iid in self.datasheet.selection()]
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self.window, samples, "Compare SNR to StdDev", title))

    def f_rename_sample(self):
        s = self.datasheet.focus()
        if s:
            new_name = ""
            while not new_name or new_name in [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.get_children()]:
                new_name = tk.simpledialog.askstring(f"Rename {self.datasheet.item(s)['values'][0]}", "Enter new title (must be unique)")
            v = self.datasheet.item(s)["values"]
            v[0] = new_name
            self.datasheet.item(s, values=v)

    def f_delete_selected(self):
        samples = [iid for iid in self.datasheet.selection()]
        self.datasheet.delete(*samples)

    def f_delete_all(self):
        self.datasheet.delete(*self.datasheet.get_children())

    def f_open(self):
        initial_dir = "/"
        if "directory" in self.parent_app.args:
            initial_dir = self.parent_app.args["directory"]
        file = tk.filedialog.askopenfilename(defaultextension=".pkl", initialdir=initial_dir)

        with open(file, "rb") as f:
            samples = pickle.load(f)

        for s in samples:
            title = s
            if s.startswith("Measurement"):
                title = ""
            if s in [self.datasheet.item(child)["values"][0] for child in self.datasheet.get_children()]:
                title = title + "_1"
            self.add_sample(samples[s], title=title)

    def f_save_selected(self):       # Uses pickle for now, TODO: change to more accessible format, maybe json or csv
        initial_dir = "/"
        if "directory" in self.parent_app.args:
            initial_dir = self.parent_app.args["directory"]
        file = tk.filedialog.asksaveasfilename(defaultextension=".pkl", initialdir=initial_dir)

        samples = {}

        for child in self.datasheet.get_children():
            samples[self.datasheet.item(child)["values"][0]] = self.data[child]

        with open(file, "wb") as f:
            pickle.dump(samples, f)

    # Event Handling

    def sort_by_column(self, col, reverse):
        try:
            l = [(float(self.datasheet.set(k, col)), k) for k in self.datasheet.get_children("")]
        except ValueError:
            l = [(self.datasheet.set(k, col), k) for k in self.datasheet.get_children("")]

        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.datasheet.move(k, "", index)

        self.datasheet.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, not reverse))

    def on_closing(self):
        self.window.withdraw()


class GraphWindow:
    def __init__(self, parent, samples, graph_type, title):
        self.samples = samples
        self.title = title
        self.graph_type = graph_type

        self.parent = parent
        self.window = tk.Toplevel()
        self.window.withdraw()

        self.window.title(graph_type + ": " + ", ".join(title))
        self.window.geometry = "800x600"

        self.normalize = tk.BooleanVar()
        self.interval = tk.IntVar()

        self.canvas = None

        self.f = Figure(dpi=200)

        if graph_type == "t-S-Graph" or graph_type == "Compare SNR to StdDev":
            self.slider = tk.Scale(self.window, from_=1, to=max(len(sample.data[0]) for sample in samples) // 2, orient=tk.HORIZONTAL, variable=self.interval, label="Interval for moving average: ")
            self.slider.bind("<ButtonRelease-1>", lambda x: self._redraw())
            self.slider.pack(fill=tk.BOTH, expand=True)

        self.normalize_check = tk.Checkbutton(self.window, variable=self.normalize, offvalue=False, onvalue=True, text="Normalize", command=self._redraw)

        self.normalize_check.pack(side=tk.LEFT)

        self.draw_figure(self.f, samples, graph_type)

        self.window.deiconify()

    def draw_figure(self, f, samples, graph_type, interval=1, normalize=False):
        if graph_type == "t-S-Graph":
            data = [sample.get_flattened_moving_average(interval) for sample in samples]
            axis_x = [i for i in range(interval, interval + max(map(len, data)))]

            f.clear()

            a = f.add_subplot(111)
            a.set_ylabel("ADUs")
            a.set_xlabel("Pixel from Start")

            for d, t in zip(data, self.title):
                if normalize: d = d / np.mean(d)
                a.plot(axis_x, d, label=t)

            a.legend()

        elif graph_type == "Show Crosssection":
            data = [sample.get_crosssection() for sample in samples]

            f.clear()

            a = f.add_subplot(111)

            a.set_ylabel("ADUs")
            a.set_xlabel("Pixel from Centre")

            for d, t in zip(data, self.title):
                if normalize: d = d / np.max(d)
                offset = list(d).index(max(d))
                a.plot(np.array([i for i in range(len(d))]) - offset, d, label=t)

            a.legend()

        else:
            raise ValueError

        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.f, self.window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _redraw(self):
        self.draw_figure(self.f, self.samples, self.graph_type, interval=self.interval.get(), normalize=self.normalize.get())
