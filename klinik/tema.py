# -*- coding: utf-8 -*-
"""Ortak tema + tablo yardımcısı. Her sekme buradaki düzeni kullanır."""
from tkinter import ttk


def tema_uygula(kok):
    st = ttk.Style(kok)
    try:
        st.theme_use("clam")
    except Exception:
        pass
    st.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(12, 8))
    st.configure("TButton", font=("Segoe UI", 10), padding=6)
    st.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
    st.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e2e8f0")
    st.configure("Title.TLabel", font=("Segoe UI", 11, "bold"))
    st.configure("Card.TFrame", background="#f1f5f9", relief="raised", borderwidth=1)


def tablo_duzeni(tree):
    tree.tag_configure("odd", background="#f8fafc")
    tree.tag_configure("even", background="#ffffff")
    tree.tag_configure("kritik", background="#fee2e2")
    tree.tag_configure("ok", background="#dcfce7")


def cift_tag(i):
    return ("even" if i % 2 else "odd",)


def tablo_kur(ebeveyn, sutunlar):
    tree = ttk.Treeview(ebeveyn, columns=[k for k, _, _ in sutunlar], show="headings")
    for k, baslik, genislik in sutunlar:
        tree.heading(k, text=baslik)
        tree.column(k, width=genislik)
    tree.pack(fill="both", expand=True, pady=4)
    tablo_duzeni(tree)
    return tree
