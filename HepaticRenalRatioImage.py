import numpy as np
import ast
import os
import cv2
from collections import defaultdict
import matplotlib.pyplot as plt
from pandas.core.computation.ops import isnumeric


class HepaticRenalRatioImage:
    def __init__(self, file_name, liver_locations = [], kidney_locations = [], params = None):
        if params is not None:
            self.load_from_dictionary(params)
        else:
            self.file_name = file_name
            self.liver_locations = liver_locations  # Array of (x, y, x-radius,y-radius)
            self.kidney_locations = kidney_locations  # Array of (x, y, x-radius,y-radius)
        self.liver_pixels = None
        self.kidney_pixels = None
        self.liver_mean = None
        self.kidney_mean = None
        self.liver_std = None
        self.kidney_std = None
        self.hepatic_renal_ratio = None
        self.hepatic_renal_ratio_std = None

    def read_pixels(self):
        # Read the image
        image = cv2.imread(self.file_name, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Image file '{self.file_name}' not found.")
        if len(self.kidney_locations) == 0 or len(self.liver_locations) ==0:
            return None
        # Function to get unique pixel values inside circles
        def get_circle_pixels(locations):
            mask = np.zeros_like(image, dtype=bool)
            for x, y, x_radius, y_radius in locations:
                y_grid, x_grid = np.ogrid[:image.shape[0], :image.shape[1]]
                circle_mask = (((x_grid - x) / x_radius) ** 2 + ((y_grid - y) / y_radius) ** 2) <= 1
                mask |= circle_mask
            return image[mask].flatten().tolist()

        # Get unique pixel values for liver and kidney locations
        self.liver_pixels = get_circle_pixels(self.liver_locations)
        self.kidney_pixels = get_circle_pixels(self.kidney_locations)

        # Calculate statistics
        if len(self.liver_pixels) > 0:
            self.liver_mean = np.mean(self.liver_pixels)
            self.liver_std = np.std(self.liver_pixels)
        if len(self.kidney_pixels) > 0:
            self.kidney_mean = np.mean(self.kidney_pixels)
            self.kidney_std = np.std(self.kidney_pixels)

        # Calculate hepatic-renal ratio and standard deviation
        if self.kidney_mean is not None and isnumeric(self.kidney_mean) and self.kidney_mean > 0:
            self.hepatic_renal_ratio = self.liver_mean / self.kidney_mean
            self.hepatic_renal_ratio_std = np.sqrt(
                (self.liver_std / self.liver_mean)**2 + (self.kidney_std / self.kidney_mean)**2
            ) * self.hepatic_renal_ratio

        return True # That is, success
    def get_parameters(self):
        return {
            "file_name": self.file_name,
            "liver_locations": self.liver_locations,
            "kidney_locations": self.kidney_locations,
            "liver_pixels": self.liver_pixels,
            "kidney_pixels": self.kidney_pixels,
            "liver_mean": self.liver_mean,
            "kidney_mean": self.kidney_mean,
            "liver_std": self.liver_std,
            "kidney_std": self.kidney_std,
            "hepatic_renal_ratio": self.hepatic_renal_ratio,
            "hepatic_renal_ratio_std": self.hepatic_renal_ratio_std
        }
    def load_from_dictionary(self, params):
        self.file_name = params.get("file_name", None)
        self.liver_locations = params.get("liver_locations", [])
        self.kidney_locations = params.get("kidney_locations", [])
        self.liver_pixels = params.get("liver_pixels", [])
        self.kidney_pixels = params.get("kidney_pixels", [])
        self.liver_mean = params.get("liver_mean", None)
        self.kidney_mean = params.get("kidney_mean", None)
        self.liver_std = params.get("liver_std", None)
        self.kidney_std = params.get("kidney_std", None)
        self.hepatic_renal_ratio = params.get("hepatic_renal_ratio", None)
        self.hepatic_renal_ratio_std = params.get("hepatic_renal_ratio_std", None)

        # Convert everything to python lists.
        # This is bad coding, but works
        # Probably better to use some sort of json.loads
        self.liver_locations = ast.literal_eval(self.liver_locations) if type(self.liver_locations) is str else self.liver_locations
        self.kidney_locations = ast.literal_eval(self.kidney_locations) if type(self.kidney_locations) is str else self.kidney_locations
        self.liver_pixels = ast.literal_eval(self.liver_pixels) if type(self.liver_pixels) is str else self.liver_pixels
        self.kidney_pixels = ast.literal_eval(self.kidney_pixels) if type(self.kidney_pixels) is str else self.kidney_pixels

    def create_picture_with_histograms(self, path = None):
        # if not self.liver_pixels or not self.kidney_pixels:
        #     raise ValueError("Pixel data is empty. Ensure 'read_pixels' is called before creating histograms.")
        self.read_pixels()
        # Convert pixel data to numpy arrays
        liver_data = np.array(self.liver_pixels)
        kidney_data = np.array(self.kidney_pixels)

        # Create histograms
        fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

        axes[0].hist(liver_data, bins=30, color='blue', alpha=0.7)
        axes[0].set_title("Liver Pixels")
        axes[0].set_xlabel("Pixel Intensity")
        axes[0].set_ylabel("Frequency")
        axes[0].text(0.95, 0.95, f"Mean: {liver_data.mean():.2f}\nStd: {liver_data.std():.2f}",
                     transform=axes[0].transAxes, ha="right", va="top", fontsize=10,
                     bbox=dict(facecolor="white", alpha=0.5))

        axes[1].hist(kidney_data, bins=30, color='yellow', alpha=0.7)
        axes[1].set_title("Kidney Pixels")
        axes[1].set_xlabel("Pixel Intensity")
        axes[1].text(0.95, 0.95, f"Mean: {kidney_data.mean():.2f}\nStd: {kidney_data.std():.2f}",
                     transform=axes[1].transAxes, ha="right", va="top", fontsize=10,
                     bbox=dict(facecolor="white", alpha=0.5))

        # Adjust layout
        plt.tight_layout()

        # Save the figure
        base_name, _ = os.path.splitext(self.file_name)
        output_path = f"{base_name}_histograms.tif" if path is None else path
        fig.suptitle(self.file_name)
        plt.savefig(output_path)
        plt.close(fig)

        print(f"Histogram figure saved to: {output_path}")

