import tkinter as tk
from tkinter import filedialog

import numpy as np
import rx
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure
from rx.operators import debounce

from slider import Slider


class ImageEditor(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.image = None
        self.width = 0
        self.height = 0
        self.values = None
        self.points = None

        self.canvas_width = 600
        self.canvas_height = 600

        self.fig = Figure(figsize=(7, 7), dpi=100)
        self.plot1 = self.fig.add_subplot(111)
        # self.plot1.set_aspect('equal')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(column=0, row=0, rowspan=9, sticky="W")

        self.load_button = tk.Button(self, text="Load Image", command=self.load_image)
        self.load_button.grid(column=1, row=0, sticky="W")

        self.create_controls()
        self.grid_columnconfigure(0, weight=1)

    def load_image(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            file = open(file_path, 'r')
            self.points = file.readlines()
            file.close()
            self.render_image()

    def render_image(self):
        if not self.points:
            return

        if not self.values:
            return

        self.update_image(self.values)

    @staticmethod
    def transform_points(points, rotation_xy, z_near, z_far, dx, dy, k1, cam_x, cam_y):
        object = []

        for s in points:
            s += ' 1'
            object.append(s.split())

        object = np.array(object).astype(float)

        angle_sin = np.sin(rotation_xy)
        angle_cos = np.cos(rotation_xy)

        z_range = z_far - z_near

        P = np.array([[angle_cos, -angle_sin, dx, 0], [angle_sin, angle_cos, dy, 0],
                      [0, 0, -z_far / z_range, z_near * z_far / z_range], [0, 0, 1, 0]])
        Cam = np.array([[cam_x, 0, 0, 0], [0, cam_y, 0, 0], [0, 0, 1, 0]])

        dots = []

        for i in range(object.shape[0]):
            f = Cam @ P @ object[i, :]
            dots.append(f / f[2])
        dots = np.array(dots)

        dots_center = np.array([0.1, 0.1])

        r = (dots[:, :2] - dots_center) ** 2

        f1 = r.sum(axis=1)
        f2 = (r ** 2).sum(axis=1)

        K2 = 0

        mask = np.expand_dims(k1 * f1 + K2 * f2, axis=-1)
        dots_new = (dots[:, :2]) + (dots[:, :2] - dots_center) * mask

        return (dots_new[:, 0], dots_new[:, 1]), (dots[:, 0], dots[:, 1])

    def draw_model(self, points):
        self.plot1.clear()
        self.plot1.plot(points[0][0], points[0][1], '-D')
        self.canvas.draw()

    def create_controls(self):
        self.rotate_xy_slider = Slider(self, "Rotation XY", 0, 2 * np.pi, 0)
        self.rotate_xy_slider.grid(column=1, row=1)
        self.z_near_slider = Slider(self, "Z Near", -100, 100, -3)
        self.z_near_slider.grid(column=1, row=2)
        self.z_far_slider = Slider(self, "Z Far", -100, 100, -10)
        self.z_far_slider.grid(column=1, row=3)
        self.dx_slider = Slider(self, "dX", -100, 100, 0)
        self.dx_slider.grid(column=1, row=4)
        self.dy_slider = Slider(self, "dY", -100, 100, 0)
        self.dy_slider.grid(column=1, row=5)

        self.k1_slider = Slider(self, "K1", -100, 100, 0)
        self.k1_slider.grid(column=2, row=3)

        self.c1_slider = Slider(self, "Cam X", -10, 10, 0.5)
        self.c1_slider.grid(column=2, row=4)

        self.c2_slider = Slider(self, "Cam Y", -10, 10, 0.5)
        self.c2_slider.grid(column=2, row=5)

        rx.combine_latest(
            self.rotate_xy_slider.observable,
            self.z_near_slider.observable,
            self.z_far_slider.observable,
            self.dx_slider.observable,
            self.dy_slider.observable,
            self.k1_slider.observable,
            self.c1_slider.observable,
            self.c2_slider.observable,
        ).pipe(debounce(.5)).subscribe(self.update_image)

    def update_image(self, values):
        self.values = values
        if not self.points:
            return
        print("Updating image with values:", values)
        print(self.points)
        transformed_points = self.transform_points(self.points, *values)
        self.draw_model(transformed_points)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Image Editor")

    ImageEditor(root).place(x=0, y=0, relwidth=1, relheight=1)

    root.mainloop()
