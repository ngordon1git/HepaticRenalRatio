import tkinter as tk
#import ast
from tkinter import Canvas
from tkinter import messagebox
from HepaticRenalRatioImage import HepaticRenalRatioImage
import cv2
from PIL import Image, ImageTk

class HepaticRenalRatioAnalyzer():
    def __init__(self, hrr_image: HepaticRenalRatioImage, single_image_analysis=True,root = None):
        self.hrr_image = hrr_image
        self.single_image_analysis = single_image_analysis
        self.current_mode = "Liver"  # Default mode
        self.circles = {"Liver": self.hrr_image.liver_locations, "Kidney": self.hrr_image.kidney_locations}

        # Load and resize image for display
        self.image = cv2.imread(self.hrr_image.file_name)
        if self.image is None:
            raise FileNotFoundError(f"Image file '{self.hrr_image.file_name}' not found.")
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.display_image = Image.fromarray(self.image)

        # Initialize GUI
        if root is None:
            self.root = tk.Tk()
            self.root.title("Hepatic Renal Ratio Analyzer")
            self.root.geometry("800x600")
        else:
            self.root = root

        # Create menu area
        self.menu_frame = tk.Frame(self.root, height=90, bg="lightgray")
        self.menu_frame.pack(fill=tk.X, side=tk.TOP)
        self.create_menu()

        # Create image display area
        self.canvas = Canvas(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.update_image()

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.start_circle)
        self.canvas.bind("<B1-Motion>", self.update_circle)
        self.canvas.bind("<ButtonRelease-1>", self.complete_circle)
        self.canvas.bind("<Button-3>", self.remove_circle)

        self.canvas.bind("<Configure>", lambda event: self.update_image())


        self.start_x = self.start_y = None
        self.current_circle = None
        if self.root is None:
            self.root.bind_all("<space>", self.toggle_mode)
            self.root.mainloop()

    def create_menu(self):
        # Switch for Liver/Kidney
        self.mode_label = tk.Label(self.menu_frame, text=f"Mode: {self.current_mode}", bg="lightgray",
                                   font=("Arial", 14))
        self.mode_label.pack(side=tk.LEFT, padx=20)

        # Clear All button
        self.clear_button = tk.Button(self.menu_frame, text="Clear All", font=("Arial", 14), command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=20)

        # Analyze button (if single_image_analysis is True)
        if self.single_image_analysis:
            self.analyze_button = tk.Button(self.menu_frame, text="Analyze", font=("Arial", 14), command=self.analyze)
            self.analyze_button.pack(side=tk.RIGHT, padx=20)

    def toggle_mode(self, event=None):
        self.current_mode = "Kidney" if self.current_mode == "Liver" else "Liver"
        self.mode_label.config(text=f"Mode: {self.current_mode}")

    def update_image(self):
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width() or self.root.winfo_width()
        canvas_height = self.canvas.winfo_height() or self.root.winfo_height()

        # Compute the scaling factors
        self.scale_x = canvas_width / self.image.shape[1]
        self.scale_y = canvas_height / self.image.shape[0]

        # Resize the image to fit the canvas
        resized_width = int(self.image.shape[1] * self.scale_x)
        resized_height = int(self.image.shape[0] * self.scale_y)
        self.resized_image = self.display_image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

        # Display the resized image
        self.tk_image = ImageTk.PhotoImage(self.resized_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        self.redraw_circles()

    def start_circle(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.current_circle = self.canvas.create_oval(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="blue" if self.current_mode == "Liver" else "yellow",
            fill="",
            width=2
        )

    def update_circle(self, event):
        if self.current_circle:
            self.canvas.coords(
                self.current_circle,
                self.start_x, self.start_y, event.x, event.y
            )

    def complete_circle(self, event):
        if self.current_circle:
            # Get display coordinates
            x0, y0, x1, y1 = self.canvas.coords(self.current_circle)

            # Calculate circle center and radius in display coordinates
            cx_display, cy_display = (x0 + x1) / 2, (y0 + y1) / 2
            # radius_display = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / 2
            radius_x_display = (x1 - x0) / 2
            radius_y_display = (y1 - y0) / 2

            # Map to full-image coordinates
            cx_full = int(cx_display / self.scale_x)
            cy_full = int(cy_display / self.scale_y)
            # radius_full = int(radius_display / self.scale_x)  # Assuming uniform scaling
            radius_x_full = int(radius_x_display / self.scale_x)
            radius_y_full = int(radius_y_display / self.scale_y)

            # Save the circle
            if radius_x_full > 0 and radius_y_full > 0:
                self.circles[self.current_mode].append((cx_full, cy_full, radius_x_full, radius_y_full))

            # The following code is not necessary, as the previous line already does that.
            # It's a class, and hold reference to liver_locations, therefore, adding it to @self.circles[mode] does the trick
            # if self.current_mode == "Liver":
            #     self.hrr_image.liver_locations.append((cx_full, cy_full, radius_x_full, radius_y_full))
            # else:
            #     self.hrr_image.kidney_locations.append((cx_full, cy_full, radius_x_full, radius_y_full))

            self.current_circle = None

    def remove_circle(self, event):
        if self.circles[self.current_mode]:
            # Remove last circle from canvas and data
            last_circle = self.circles[self.current_mode].pop()
            if self.current_mode == "Liver":
                self.hrr_image.liver_locations.pop()
            else:
                self.hrr_image.kidney_locations.pop()
            self.canvas.delete("all")
            self.update_image()
            self.redraw_circles()

    def redraw_circles(self):
        # Get scaling ratios
        original_width, original_height = self.image.shape[1], self.image.shape[0]
        displayed_width, displayed_height = self.canvas.winfo_width(), self.canvas.winfo_height()

        x_ratio = displayed_width / original_width
        y_ratio = displayed_height / original_height

        for mode, color in [("Liver", "blue"), ("Kidney", "yellow")]:
            # cs = ast.literal_eval(self.circles[mode]) if type(self.circles[mode]) is str else self.circles[mode]
            for cx, cy, radius_x, radius_y in self.circles[mode]:
                scaled_cx = cx * x_ratio
                scaled_cy = cy * y_ratio
                scaled_radius_x = radius_x * x_ratio
                scaled_radius_y = radius_y * y_ratio
                self.canvas.create_oval(
                    scaled_cx - scaled_radius_x, scaled_cy - scaled_radius_y,
                    scaled_cx + scaled_radius_x, scaled_cy + scaled_radius_y,
                    outline=color, fill="", width=2
                )

    def clear_all(self):
        # Clear all circles and reset data
        self.circles = {"Liver": [], "Kidney": []}
        self.hrr_image.liver_locations.clear()
        self.hrr_image.kidney_locations.clear()
        self.canvas.delete("all")
        self.update_image()

    def analyze(self):
        try:
            self.hrr_image.read_pixels()
            parameters = self.hrr_image.get_parameters()
            result_message = "\n".join([f"{key}: {value}" for key, value in parameters.items()])
            messagebox.showinfo("Analysis Results", result_message)
            self.hrr_image.create_picture_with_histograms()
        except Exception as e:
            messagebox.showerror("Error", str(e))

# Example usage
if __name__ == "__main__":
    hrr_image = HepaticRenalRatioImage("ultrasound1.tif", [], [])
    HepaticRenalRatioAnalyzer(hrr_image)
