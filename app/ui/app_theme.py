"""Paleta y estilos compartidos por la aplicación y el ingreso."""
from tkinter import ttk
from app.ui.platform_support import UI_FONT
from app.ui.text_navigation import install_word_navigation
from app.ui.checkbox_style import install_checkbox_style


def apply_theme(root):
    install_word_navigation(root)
    style = ttk.Style(root)
    style.theme_use('clam')
    root.configure(background='#f3f6fb')
    style.configure('.', font=(UI_FONT, 10), background='#f3f6fb', foreground='#243449')
    style.configure('TFrame', background='#f3f6fb')
    style.configure('TLabel', background='#f3f6fb')
    style.configure('Title.TLabel', font=(UI_FONT, 18, 'bold'), foreground='#153e65')
    style.configure('Section.TLabel', font=(UI_FONT, 11, 'bold'), foreground='#126b78',
                    background='#e2f2f2', padding=(10, 9))
    style.configure('TEntry', fieldbackground='white', padding=6, bordercolor='#cbd7e5')
    style.map('TEntry', bordercolor=[('focus', '#168b96')])
    style.configure('TCombobox', padding=5, fieldbackground='white')
    style.configure('TButton', padding=(10, 7), background='#e3ebf5', borderwidth=0)
    style.map('TButton', background=[('active', '#cbdced'), ('pressed', '#b6ccdf')])
    style.configure('Primary.TButton', background='#147d8b', foreground='white', font=(UI_FONT, 10, 'bold'))
    style.map('Primary.TButton', background=[('disabled', '#afbdc9'), ('active', '#106675')],
              foreground=[('disabled', '#f3f6fb')])
    install_checkbox_style(root, style)
    style.configure('TScrollbar', background='#becfdf', troughcolor='#e8eef5', borderwidth=0)
    style.layout('Choice.TRadiobutton', [('Button.border', {'sticky': 'nswe', 'children': [
        ('Radiobutton.padding', {'children': [
            ('Radiobutton.label', {'sticky': 'nswe'})], 'sticky': 'nswe'})]})])
    style.configure('Choice.TRadiobutton', padding=(10, 7), background='#e3ebf5', anchor='center',
                    borderwidth=3, relief='solid')
    # Reservar el borde evita que el botón cambie de tamaño al recibir el foco.
    choice_border = [('focus', '#153e65'), ('selected', '#147d8b'),
                     ('active', '#cbdced'), ('!focus', '#e3ebf5')]
    style.map('Choice.TRadiobutton', background=[('selected', '#147d8b'), ('active', '#cbdced')],
              foreground=[('selected', 'white')], bordercolor=choice_border,
              lightcolor=choice_border, darkcolor=choice_border)
