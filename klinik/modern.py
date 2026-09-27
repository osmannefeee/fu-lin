# -*- coding: utf-8 -*-
"""Modern arayüz uyumluluk katmanı: ttk benzeri API ile CustomTkinter widget'ları.

Kullanım: `from tkinter import ttk` yerine `from .modern import ttk`
(ttk.Notebook / Treeview / Style aynen korunur; diğerleri modernleşir).
"""
import customtkinter as _ctk
from tkinter import ttk as _ttk

Notebook = _ttk.Notebook
Treeview = _ttk.Treeview
Style = _ttk.Style

_STIL_RENK = {
    "Accent": "#0ea5e9",
    "Success": "#10b981",
    "Danger": "#ef4444",
}


def _px(width):
    if isinstance(width, int) and 0 < width <= 80:
        return width * 7
    return width


class Frame(_ctk.CTkFrame):
    def __init__(self, master=None, padding=None, style=None, **kw):
        super().__init__(master, **kw)


class Label(_ctk.CTkLabel):
    def __init__(self, master=None, style=None, **kw):
        if style and "Big" in style:
            kw.setdefault("font", ("Segoe UI", 14, "bold"))
        elif style and "Title" in style:
            kw.setdefault("font", ("Segoe UI", 11, "bold"))
        super().__init__(master, **kw)


class Button(_ctk.CTkButton):
    def __init__(self, master=None, style=None, **kw):
        for ad, renk in _STIL_RENK.items():
            if style and ad in style:
                kw.setdefault("fg_color", renk)
                break
        super().__init__(master, **kw)


class Entry(_ctk.CTkEntry):
    def __init__(self, master=None, width=None, **kw):
        if width is not None:
            kw["width"] = _px(width)
        super().__init__(master, **kw)


class Combobox(_ctk.CTkComboBox):
    def __init__(self, master=None, values=(), state=None, width=None, **kw):
        if width is not None:
            kw["width"] = _px(width)
        super().__init__(master, values=list(values or []), **kw)


class Toplevel(_ctk.CTkToplevel):
    pass


class _TtkModul:
    """`ttk.X` erişimlerini modern sürümlere yönlendirir."""

    Notebook = Notebook
    Treeview = Treeview
    Style = Style
    Frame = Frame
    Label = Label
    Button = Button
    Entry = Entry
    Combobox = Combobox
    Toplevel = Toplevel


ttk = _TtkModul()
