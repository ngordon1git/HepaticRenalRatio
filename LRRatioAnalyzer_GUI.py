import os
import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
from HepaticRenalRatioAnalyzeGUI import HepaticRenalRatioAnalyzer
from HepaticRenalRatioImage import HepaticRenalRatioImage

class HepaticRenalRatioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hepatic Renal Ratio Analyzer")
        self.geometry("1000x600")

        self.image_instances = []
        self.current_path = ""
        self.current_file_index = None
        self.current_analyzer = None
        self.create_widgets()

    def create_widgets(self):
        # Menu frame
        self.menu_frame = tk.Frame(self, height=50, bg="lightgray")
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Button(self.menu_frame, text="Choose Path", command=self.choose_path).pack(side=tk.LEFT, padx=5, pady=5)
        self.create_histograms_var = tk.BooleanVar()
        tk.Checkbutton(self.menu_frame, text="Create Histograms", variable=self.create_histograms_var).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.menu_frame, text="Analyze All", command=self.analyze_all).pack(side=tk.LEFT, padx=5, pady=5)

        # Main content frame
        self.main_content_frame = tk.Frame(self)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable list of file names
        self.file_list_frame = tk.Frame(self.main_content_frame, width=200)
        self.file_list_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.file_list_frame.pack_propagate(False)

        self.file_listbox = tk.Listbox(self.file_list_frame, selectmode=tk.SINGLE)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)

        scrollbar = tk.Scrollbar(self.file_list_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # Analyzer widget
        self.analyzer_frame = tk.Frame(self.main_content_frame)
        self.analyzer_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        # Bind key events globally
        self.bind("<space>", self.on_space_press)


    def choose_path(self):
        self.current_path = filedialog.askdirectory()
        if not self.current_path:
            return

        self.load_or_create_excel()
        self.populate_file_list()

    def load_or_create_excel(self):
        excel_path = os.path.join(self.current_path, "LRR_results.xlsx")

        if os.path.exists(excel_path):
            data = pd.read_excel(excel_path)
            # self.image_instances = [HepaticRenalRatioImage(row['file_name']) for _, row in data.iterrows()]
            self.image_instances = [HepaticRenalRatioImage(file_name = '', params=row) for _, row in data.iterrows()]

        else:
            tif_files = [f for f in os.listdir(self.current_path) if f.endswith('.tif')]
            self.image_instances = [HepaticRenalRatioImage(os.path.join(self.current_path, f)) for f in tif_files]

            data = pd.DataFrame([i.get_parameters() for i in self.image_instances]).set_index('file_name')
            data.to_excel(excel_path, index=True)
            # Following the cration of an excel, load it.
            self.load_or_create_excel()

    def populate_file_list(self):
        self.file_listbox.delete(0, tk.END)

        for img in self.image_instances:
            color = "black"
            if not img.liver_locations or not img.kidney_locations:
                color = "black"
            elif img.liver_mean is None or img.kidney_mean is None:
                color = "red"
            else:
                color = "green"

            self.file_listbox.insert(tk.END, os.path.basename(img.file_name))
            self.file_listbox.itemconfig(tk.END, fg=color)

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if self.current_file_index is not None:
            self.update_excel()
            # Delete circles on screen


        self.current_file_index = index
        self.display_analyzer(self.image_instances[index])

    def update_excel(self):
        if self.current_file_index is None:
            return

        excel_path = os.path.join(self.current_path, "LRR_results.xlsx")
        data = pd.read_excel(excel_path).set_index('file_name')
        img = self.image_instances[self.current_file_index]
        img_dic = img.get_parameters()
        img_dic = dict((i, img_dic[i]) for i in img_dic if i not in ['file_name', 'kidney_pixels','liver_pixels']) # remove index..
        data.loc[img.file_name] = img_dic
         # data.loc[img.file_name] = img.get_parameters()
        # data.loc[self.current_file_index, 'hepatic_renal_ratio'] = img.calculate_hepatic_renal_ratio() if img.liver_mean and img.kidney_mean else None
        data.to_excel(excel_path, index=True)

    def display_analyzer(self, image_instance):
        if isinstance(image_instance, HepaticRenalRatioImage) and self.current_analyzer and image_instance is self.current_analyzer.hrr_image:
            return
        for widget in self.analyzer_frame.winfo_children():
            widget.destroy()

        if isinstance(image_instance, HepaticRenalRatioImage):
            self.current_analyzer = HepaticRenalRatioAnalyzer(image_instance, root = self.analyzer_frame)
            # self.current_analyzer.pack(fill=tk.BOTH, expand=True)
    def on_space_press(self, event):
        if self.current_analyzer is not None:
            self.current_analyzer.toggle_mode()

    def analyze_all(self):
        results_path = os.path.join(self.current_path, "results")
        os.makedirs(results_path, exist_ok=True)

        for img in self.image_instances:
            flag = img.read_pixels() # None / False if no locations are chosen for both liver and kidney

            if flag and self.create_histograms_var.get():
                histogram_path = os.path.join(results_path, f"{os.path.basename(img.file_name)}_histogram.png")
                img.create_picture_with_histograms(path = histogram_path)
        self.update_excel()
        self.populate_file_list()

if __name__ == "__main__":
    app = HepaticRenalRatioApp()
    app.mainloop()
