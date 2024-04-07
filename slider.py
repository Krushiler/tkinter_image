import tkinter as tk

from rx.subject import BehaviorSubject


class Slider(tk.Frame):
    def __init__(self, master, text, min_val, max_val, default_val):
        tk.Frame.__init__(self, master)
        self.min_val = min_val
        self.max_val = max_val
        self.default_val = default_val

        self.var = tk.DoubleVar()
        self.var.set(default_val)
        self.text = text

        self.label = tk.Label(self, text=self.text)
        self.label.pack()

        self.slider = tk.Scale(self, from_=min_val, to=max_val, orient="horizontal", variable=self.var,
                               command=self.update_text, resolution=0.01)
        self.slider.pack()

        self.entry = tk.Entry(self, textvariable=self.var)
        self.entry.pack()
        self.entry.bind('<Return>', self.update_slider)

        self.observable = BehaviorSubject(default_val)

    def update_text(self, value):
        self.var.set(float(value))
        self.observable.on_next(float(value))

    def update_slider(self, event):
        try:
            value = float(self.entry.get())
            if value < self.min_val:
                value = self.min_val
            elif value > self.max_val:
                value = self.max_val
            self.slider.set(value)
            self.observable.on_next(float(value))
        except ValueError:
            pass
