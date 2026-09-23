"""Indicadores de casilla compartidos, escalados según la pantalla de Tk."""
import math
import tkinter as tk


def _indicator(root, size, *, selected=False, alternate=False, active=False,
               focused=False, disabled=False):
    image = tk.PhotoImage(master=root, width=size + 6, height=size)
    border = '#b8c5d1' if disabled else '#147d8b' if active or selected or alternate else '#899eaf'
    fill = '#e5ebf0' if disabled else '#106675' if active and selected else '#147d8b' if selected or alternate else '#ffffff'
    mark = '#8a9aa8' if disabled else '#ffffff'

    def rounded(x, y, inset, radius):
        # Distancia a un rectángulo redondeado en una cuadrícula de 28 unidades.
        center = 14
        half = center - inset
        dx = max(abs(x - center) - (half - radius), 0)
        dy = max(abs(y - center) - (half - radius), 0)
        return dx * dx + dy * dy <= radius * radius

    def on_line(x, y, start, end):
        ax, ay = start
        bx, by = end
        t = max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) /
                       ((bx - ax) ** 2 + (by - ay) ** 2)))
        return math.hypot(x - ax - t * (bx - ax), y - ay - t * (by - ay)) <= 1.25

    for py in range(size):
        for px in range(size):
            x, y = (px + .5) * 28 / size, (py + .5) * 28 / size
            color = None
            if focused and not disabled and rounded(x, y, 0, 7) and not rounded(x, y, 1.3, 6):
                color = '#147d8b'
            if rounded(x, y, 3, 4):
                color = border
            if rounded(x, y, 4.5, 2.5):
                color = fill
            if selected and (on_line(x, y, (8, 14), (12, 18)) or on_line(x, y, (12, 18), (20, 10))):
                color = mark
            elif alternate and on_line(x, y, (9, 14), (19, 14)):
                color = mark
            if color:
                image.put(color, (px, py))
    return image


def install_checkbox_style(root, style):
    element = 'Rounded.Checkbutton.indicator'
    if element not in style.element_names():
        size = max(24, round(21 * float(root.tk.call('tk', 'scaling'))))
        images = []
        states = []
        for disabled, focused, active in [(True, False, False), (False, True, True),
                                          (False, True, False), (False, False, True),
                                          (False, False, False)]:
            for value in ('selected', 'alternate', 'off'):
                image = _indicator(root, size, selected=value == 'selected', alternate=value == 'alternate',
                                   disabled=disabled, focused=focused, active=active)
                images.append(image)
                state = ['disabled' if disabled else '!disabled',
                         'focus' if focused else '!focus', 'active' if active else '!active']
                if disabled:
                    state = ['disabled']
                state += ['selected'] if value == 'selected' else ['!selected', 'alternate'] if value == 'alternate' else ['!selected', '!alternate']
                states.append((*state, image))
        # Tk conserva nombres de imágenes; mantener vivos también los objetos Python.
        root._checkbox_images = images
        style.element_create(element, 'image', images[-1], *states, sticky='w')
    style.layout('TCheckbutton', [('Checkbutton.padding', {'sticky': 'nswe', 'children': [
        (element, {'side': 'left', 'sticky': ''}),
        ('Checkbutton.label', {'side': 'left', 'sticky': 'w'}),
    ]})])
    style.configure('TCheckbutton', padding=(6, 5), background='#f3f6fb',
                    foreground='#243449', anchor='w')
    style.map('TCheckbutton', background=[('disabled', '#f3f6fb'), ('active', '#e2f2f2')],
              foreground=[('disabled', '#8796a5')])
