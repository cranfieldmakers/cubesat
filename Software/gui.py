import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import subprocess
import os
import re
import ast
import numpy as np
from matplotlib.colors import ListedColormap


class LogFileReader:
    def __init__(self, file_path, start_byte, end_byte):
        self.file_path = file_path
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.buffer = ""
        self.last_processed = set()  # Store processed (timestamp, phase_key, data_key)

    def read_new_lines(self):
        new_lines = []
        with open(self.file_path, 'r') as file:
            lines = file.readlines()

        new_data = ''.join(lines)
        self.buffer += new_data

        while self.start_byte in self.buffer and self.end_byte in self.buffer:
            start_index = self.buffer.find(self.start_byte)
            end_index = self.buffer.find(self.end_byte) + len(self.end_byte)
            message = self.buffer[start_index:end_index]
            timestamp, phase_key, data_key, _ = self.extract_timestamp(message)
            if (timestamp, phase_key, data_key) not in self.last_processed:
                new_lines.append(message)
                self.last_processed.add((timestamp, phase_key, data_key))
            self.buffer = self.buffer[end_index:]

        return new_lines

    def extract_timestamp(self, message):
        pattern = re.escape(self.start_byte) + r'(.*?)' + re.escape(self.end_byte)
        match = re.search(pattern, message, re.DOTALL)
        if match:
            content = match.group(1)
            parts = content.split(',', 3)  # Split only on the first three commas
            timestamp = float(parts[0])
            phase_key = int(parts[1])
            data_key = int(parts[2])
            data = ast.literal_eval(parts[3])  # Convert string representation of list back to list
            return timestamp, phase_key, data_key, data
        return None, None, None, None


class GUI:
    def __init__(self, root, file_reader):
        self.root = root
        self.file_reader = file_reader
        self.start_time = None
        self.create_widgets()
        self.update_gui()

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.grid(row=0, column=0, sticky="nsew")

        self.phase_tabs = {}

        phase_keys = {
            1: ["Position", "Rotation", "Axial Velocities", "Light Readings", "Grid Temperatures"],
            2: ["Classifications", "Grid Temperatures", "Position", "Rotation", "Axial Velocities"],
            3: ["Motor Speed", "Motor Direction", "Position", "Rotation", "Axial Velocities", "Heat Source Located",
                "Heat Source Centered"]
        }

        for phase, titles in phase_keys.items():
            tab = ttk.Frame(self.tab_control)
            self.tab_control.add(tab, text=f"Phase {phase}")
            self.phase_tabs[phase] = {"tab": tab, "titles": titles}
            self.create_plots(tab, titles)

        self.log_frame = ttk.Frame(self.main_frame)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.log_text = ScrolledText(self.log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=1)

        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=3)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.launch_git_bash()

    def create_plots(self, tab, titles):
        tab.plots = []
        tab.data = [[] for _ in range(len(titles))]  # Initialize data storage for each plot
        for i, title in enumerate(titles):
            fig = plt.Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            ax.set_title(title)
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="nsew")
            tab.plots.append((canvas, ax))
        for i in range(3):
            tab.grid_columnconfigure(i, weight=1)
        for i in range((len(titles) + 2) // 3):
            tab.grid_rowconfigure(i, weight=1)

    def update_gui(self):
        new_lines = self.file_reader.read_new_lines()
        for line in new_lines:
            self.process_line(line)
        self.root.after(1000, self.update_gui)

    def process_line(self, line):
        self.log_text.insert(tk.END, line + "\n")
        self.log_text.see(tk.END)
        timestamp, phase_key, data_key, data = self.parse_line(line)
        print(f"Read line: {line.strip()}")  # Debug statement
        print(
            f"Parsed - Timestamp: {timestamp}, Phase: {phase_key}, Data Key: {data_key}, Data: {data}")  # Debug statement
        if timestamp is not None:
            if self.start_time is None:
                self.start_time = timestamp
            tab_info = self.phase_tabs.get(phase_key)
            if tab_info:
                print(f"Updating plot for Phase {phase_key}, Data Key {data_key}")  # Debug statement
                self.update_plot(tab_info["tab"], data_key, timestamp, data, phase_key)

    def parse_line(self, line):
        # Assuming the format is {start_byte}{timestamp}{phase_key}{data_key}{data}{end_byte}
        pattern = re.escape(self.file_reader.start_byte) + r'(.*?)' + re.escape(self.file_reader.end_byte)
        match = re.search(pattern, line, re.DOTALL)
        if match:
            content = match.group(1)
            parts = content.split(',', 3)  # Split only on the first three commas
            timestamp = float(parts[0])
            phase_key = int(parts[1])
            data_key = int(parts[2])
            data = ast.literal_eval(parts[3])  # Convert string representation of list back to list
            return timestamp, phase_key, data_key, data
        return None, None, None, None

    def update_plot(self, tab, data_key, timestamp, data, phase_key):
        elapsed_time = timestamp - self.start_time
        canvas, ax = tab.plots[data_key]

        legend_labels_phase_1_2 = {
            0: ["X Position", "Y Position", "Z Position"],
            1: ["X Rotation", "Y Rotation", "Z Rotation"],
            2: ["X Velocity", "Y Velocity", "Z Velocity"],
            3: ["Light Intensity 1", "Light Intensity 2"]
        }

        legend_labels_phase_3 = {
            0: ["Motor Speed"],
            1: ["Motor Direction"],
            2: ["X Position", "Y Position", "Z Position"],
            3: ["X Rotation", "Y Rotation", "Z Rotation"],
            4: ["X Velocity", "Y Velocity", "Z Velocity"],
            5: ["Heat Source Located"],
            6: ["Heat Source Centered"]
        }

        if phase_key == 1:  # Phase 1: Telemetry Data
            if data_key in [0, 1, 2, 3]:  # Time series data
                tab.data[data_key].append((elapsed_time, data))
                x_data = [point[0] for point in tab.data[data_key]]
                y_data = [point[1] for point in tab.data[data_key]]
                ax.cla()
                labels = legend_labels_phase_1_2.get(data_key, [f"Series {idx + 1}" for idx in range(len(y_data[0]))])
                for idx, y in enumerate(zip(*y_data)):
                    ax.plot(x_data, y, label=labels[idx])
                ax.legend()
            elif data_key == 4:  # Grid temperatures (heatmap)
                ax.cla()
                cax = ax.matshow(data, cmap='hot')
                plt.colorbar(cax, ax=ax)

        elif phase_key == 2:  # Phase 2: Results Data
            if data_key == 0:  # Classifications grid
                ax.cla()
                color_map = ListedColormap(['yellow', 'green', 'red'])
                data_map = [[0 if cell == 0 else 1 if cell == 1 else 2 for cell in row] for row in data]
                ax.imshow(data_map, cmap=color_map, aspect='auto')
            elif data_key == 1:  # Grid temperatures (heatmap)
                ax.cla()
                cax = ax.matshow(data, cmap='hot')
                plt.colorbar(cax, ax=ax)
            elif data_key in [2, 3, 4]:  # Time series data
                tab.data[data_key].append((elapsed_time, data))
                x_data = [point[0] for point in tab.data[data_key]]
                y_data = [point[1] for point in tab.data[data_key]]
                ax.cla()
                labels = legend_labels_phase_1_2.get(data_key - 2, [f"Series {idx + 1}" for idx in range(len(y_data[0]))])
                for idx, y in enumerate(zip(*y_data)):
                    ax.plot(x_data, y, label=labels[idx])
                ax.legend()

        elif phase_key == 3:  # Phase 3: Other Data
            if data_key in [0, 1, 2, 3, 4]:  # Time series data
                tab.data[data_key].append((elapsed_time, data))
                x_data = [point[0] for point in tab.data[data_key]]
                y_data = [point[1] for point in tab.data[data_key]]
                ax.cla()
                labels = legend_labels_phase_3.get(data_key, [f"Series {idx + 1}" for idx in range(len(y_data[0]))])
                for idx, y in enumerate(zip(*y_data)):
                    ax.plot(x_data, y, label=labels[idx])
                ax.legend()
            elif data_key == 5:  # Heat source located
                tab.data[data_key].append((elapsed_time, data[0]))
                x_data = [point[0] for point in tab.data[data_key]]
                y_data = [point[1] for point in tab.data[data_key]]
                ax.cla()
                ax.plot(x_data, y_data, 'bo-', label="Heat Source Located")
                ax.set_ylim(-0.1, 1.1)
                ax.legend()
            elif data_key == 6:  # Heat source centered
                tab.data[data_key].append((elapsed_time, data[0]))
                x_data = [point[0] for point in tab.data[data_key]]
                y_data = [point[1] for point in tab.data[data_key]]
                ax.cla()
                ax.plot(x_data, y_data, 'bo-', label="Heat Source Centered")
                ax.set_ylim(-0.1, 1.1)
                ax.legend()

        canvas.draw()

    def launch_git_bash(self):
        subprocess.Popen(['C:\\Program Files\\Git\\git-bash.exe'])


class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Log File Path Entry")
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.label = ttk.Label(self.frame, text="Enter log file path:")
        self.label.grid(row=0, column=0, pady=5)

        self.file_path_entry = ttk.Entry(self.frame, width=50)
        self.file_path_entry.grid(row=1, column=0, pady=5)

        self.start_button = ttk.Button(self.frame, text="Start", command=self.start_application)
        self.start_button.grid(row=2, column=0, pady=5)

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def start_application(self):
        file_path = self.file_path_entry.get()
        if os.path.isfile(file_path):
            self.root.destroy()
            main_root = tk.Tk()
            main_root.title("Log File Viewer")

            main_root.grid_columnconfigure(0, weight=1)
            main_root.grid_rowconfigure(0, weight=1)

            file_reader = LogFileReader(file_path, '{', '}')
            gui = GUI(main_root, file_reader)

            main_root.mainloop()
        else:
            self.label.config(text="Invalid file path. Please try again.")


if __name__ == "__main__":
    splash_root = tk.Tk()
    splash = SplashScreen(splash_root)
    splash_root.mainloop()
