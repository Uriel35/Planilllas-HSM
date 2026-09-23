"""Visor PDF integrado con navegación, zoom y desplazamiento independiente."""
import tkinter as tk
from tkinter import ttk

from app.ui.platform_support import wheel_events

import fitz


class PdfPreview(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=14)
        self.document = None
        self.images = []
        self.zoom = 1.0
        self.render_job = None
        ttk.Label(self, text='Vista previa', style='Title.TLabel').pack(anchor='w')
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', pady=10)
        self.page_label = ttk.Label(toolbar, text='Sin planilla', width=14, anchor='center')
        self.page_label.pack(side='left')
        ttk.Button(toolbar, text='−', width=3, command=lambda: self.change_zoom(0.8)).pack(side='left', padx=(12, 0))
        ttk.Button(toolbar, text='+', width=3, command=lambda: self.change_zoom(1.25)).pack(side='left')
        ttk.Button(toolbar, text='Ajustar', command=self.fit_width).pack(side='left', padx=6)
        self.info = ttk.Label(self, text='Seleccioná una planilla.', wraplength=420)
        self.info.pack(fill='x', pady=(0, 10))
        area = ttk.Frame(self)
        area.pack(fill='both', expand=True)
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(area, background='#dce5ef', highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(area, orient='vertical', command=self.canvas.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(area, orient='horizontal', command=self.canvas.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        self.canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.canvas.bind('<Configure>', self.schedule_render)
        for event in wheel_events(self):
            self.canvas.bind(event, self.scroll)

    def scroll(self, event):
        direction = -1 if event.num == 4 or getattr(event, 'delta', 0) > 0 else 1
        self.canvas.yview_scroll(direction * 3, 'units')
        return 'break'

    def load(self, data, message, reset=False):
        document = fitz.open(stream=data, filetype='pdf')
        if self.document:
            self.document.close()
        self.document = document
        if reset:
            self.zoom = 1.0
            self.canvas.yview_moveto(0)
            self.canvas.xview_moveto(0)
        self.info.configure(text=message)
        self.render()

    def schedule_render(self, _event=None):
        if self.render_job:
            self.after_cancel(self.render_job)
        self.render_job = self.after(150, self.render)

    def render(self):
        if self.render_job:
            self.after_cancel(self.render_job)
        self.render_job = None
        if self.document is None:
            return
        width = max(200, self.canvas.winfo_width() - 24)
        # Una escala común conserva las proporciones entre páginas de distinto tamaño.
        widest = max(page.rect.width for page in self.document)
        scale = min(3.0, width / widest * self.zoom)
        position = self.canvas.yview()[0]
        self.canvas.delete('all')
        self.images = []
        top = 12
        content_width = max(width, round(widest * scale))
        for page in self.document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image = tk.PhotoImage(master=self, data=pixmap.tobytes('ppm'))
            self.images.append(image)
            left = 12 + (content_width - pixmap.width) // 2
            self.canvas.create_image(left, top, image=image, anchor='nw')
            top += pixmap.height + 20
        self.canvas.configure(scrollregion=(0, 0, content_width + 24, top))
        self.canvas.yview_moveto(position)
        count = len(self.document)
        self.page_label.configure(text=f'{count} página' if count == 1 else f'{count} páginas')

    def change_zoom(self, factor):
        self.zoom = min(3.0, max(0.5, self.zoom * factor))
        self.render()

    def fit_width(self):
        self.zoom = 1.0
        self.render()

    def destroy(self):
        if self.render_job:
            self.after_cancel(self.render_job)
        if self.document:
            self.document.close()
        super().destroy()
