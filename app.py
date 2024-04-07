import math
import tkinter as tk
from tkinter import filedialog

import numpy as np
import rx
from rx.operators import debounce
from PIL import Image, ImageTk

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

        # Создание холста
        self.canvas = tk.Canvas(self, bg="white", width=self.canvas_width, height=self.canvas_height)
        self.canvas.grid(column=0, row=0, rowspan=9, sticky="W")

        # Создание кнопки для загрузки изображения
        self.load_button = tk.Button(self, text="Load Image", command=self.load_image)
        self.load_button.grid(column=1, row=0, sticky="W")

        # Создание элементов управления для параметров
        self.create_controls()
        self.grid_columnconfigure(0, weight=1)

    def load_image(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as file:
                self.points = [tuple(map(float, line.split())) for line in file]
            self.render_image()

    def render_image(self):
        self.canvas.delete("all")

        if not self.points:
            return

        if not self.values:
            return

        self.update_image(self.values)

    @staticmethod
    def transform_points(points, rotation_xy, z_near, z_far, dx, dy, focal_length_1, focal_length_2, radial_distortion):
        transformed_points = []
        for x, y, z in points:
            # Применяем поворот XY к точкам
            rotated_x = x * math.cos(math.radians(rotation_xy)) - y * math.sin(math.radians(rotation_xy))
            rotated_y = x * math.sin(math.radians(rotation_xy)) + y * math.cos(math.radians(rotation_xy))
            rotated_z = z

            # Применяем перенос
            translated_x = rotated_x + dx
            translated_y = rotated_y + dy
            translated_z = rotated_z

            # Применяем перспективное преобразование
            transformed_x = translated_x * (focal_length_1 / (translated_z + z_near))
            transformed_y = translated_y * (focal_length_2 / (translated_z + z_near))

            # Применяем z_far
            if translated_z > z_far:
                transformed_x = transformed_x * z_far / translated_z
                transformed_y = transformed_y * z_far / translated_z

            # Применяем радиальное искажение
            r_squared = transformed_x ** 2 + transformed_y ** 2
            distorted_r = 1 + radial_distortion * r_squared
            transformed_x *= distorted_r
            transformed_y *= distorted_r

            transformed_points.append((transformed_x, transformed_y))

        return transformed_points

    def draw_model(self, points):
        self.canvas.delete(tk.ALL)

        # Находим минимальное и максимальное значения по осям X и Y
        min_x = min(points, key=lambda p: p[0])[0]
        min_y = min(points, key=lambda p: p[1])[1]
        max_x = max(points, key=lambda p: p[0])[0]
        max_y = max(points, key=lambda p: p[1])[1]

        print(len(points))
        # Определяем масштабированные координаты для каждой точки
        scaled_points = []
        for x, y in points:
            scaled_x = (x - min_x) / (max_x - min_x) * (self.canvas_width - 200) + 100
            scaled_y = (y - min_y) / (max_y - min_y) * (self.canvas_height - 200) + 100
            scaled_points.append((scaled_x, scaled_y))

        print(len(scaled_points))
        # Отрисовка модели на холсте
        # for i in range(len(scaled_points)):
        #     for j in range(i + 1, len(scaled_points)):
        #         x1, y1 = scaled_points[i]
        #         x2, y2 = scaled_points[j % len(scaled_points)]
        #         self.canvas.create_line(x1, y1, x2, y2, fill="blue")
        for i in range(len(scaled_points)):
            x1, y1 = scaled_points[i]
            self.canvas.create_oval(x1 - 5, y1 - 5, x1 + 5, y1 + 5)
            for j in range(8):
                x2, y2 = scaled_points[(i + j + 1) % len(scaled_points)]
                # self.canvas.create_line(x1, y1, x2, y2, fill="blue")

    def create_controls(self):
        # Параметры перспективного преобразования
        self.rotate_xy_slider = Slider(self, "Rotation XY", 0, 360, 0)
        self.rotate_xy_slider.grid(column=1, row=1)
        self.z_near_slider = Slider(self, "Z Near", 1, 100, 10)
        self.z_near_slider.grid(column=1, row=2)
        self.z_far_slider = Slider(self, "Z Far", 100, 1000, 500)
        self.z_far_slider.grid(column=1, row=3)
        self.dx_slider = Slider(self, "dX", -100, 100, 0)
        self.dx_slider.grid(column=1, row=4)
        self.dy_slider = Slider(self, "dY", -100, 100, 0)
        self.dy_slider.grid(column=1, row=5)

        # Параметры камеры
        self.focal_length_1_slider = Slider(self, "Focal Length 1", 1, 100, 50)
        self.focal_length_1_slider.grid(column=1, row=6)
        self.focal_length_2_slider = Slider(self, "Focal Length 2", 1, 100, 50)
        self.focal_length_2_slider.grid(column=1, row=7)

        # Параметры радиальных искажений
        self.radial_distortion_slider = Slider(self, "Radial Distortion (K1)", -1, 1, 0)
        self.radial_distortion_slider.grid(column=1, row=8)
        rx.combine_latest(
            self.rotate_xy_slider.observable,
            self.z_near_slider.observable,
            self.z_far_slider.observable,
            self.dx_slider.observable,
            self.dy_slider.observable,
            self.focal_length_1_slider.observable,
            self.focal_length_2_slider.observable,
            self.radial_distortion_slider.observable,
        ).pipe(debounce(.5)).subscribe(self.update_image)

    def update_image(self, values):
        self.values = values
        if not self.points:
            return
        print("Updating image with values:", values)
        transformed_points = self.transform_points(self.points, *values)
        self.draw_model(transformed_points)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Image Editor")

    ImageEditor(root).place(x=0, y=0, relwidth=1, relheight=1)

    root.mainloop()
