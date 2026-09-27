# -*- coding: utf-8 -*-
"""Ortak tema + tablo yardımcısı. Her sekme buradaki düzeni kullanır."""
from .modern import ttk


def tema_uygula(kok):
    st = ttk.Style(kok)
    try:
        st.theme_use("clam")
    except Exception:
        pass
    st.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(12, 8))
    st.configure("TNotebook", background="#0b1120", borderwidth=0)
    st.configure("TNotebook.Tab", background="#1a2340", foreground="#cbd5e1")
    st.map("TNotebook.Tab", background=[("selected", "#0ea5e9")],
           foreground=[("selected", "white")])
    st.configure("TButton", font=("Segoe UI", 10), padding=6)
    st.configure("Treeview", rowheight=26, font=("Segoe UI", 10),
                 background="#131a2e", fieldbackground="#131a2e", foreground="#e8eef7")
    st.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                 background="#1e2a4a", foreground="white")
    st.map("Treeview", background=[("selected", "#0ea5e9")],
           foreground=[("selected", "white")])
    st.configure("Title.TLabel", font=("Segoe UI", 11, "bold"))
    st.configure("Card.TFrame", background="#f1f5f9", relief="raised", borderwidth=1)


def tablo_duzeni(tree):
    tree.tag_configure("odd", background="#131a2e", foreground="#e8eef7")
    tree.tag_configure("even", background="#182036", foreground="#e8eef7")
    tree.tag_configure("kritik", background="#5a1f1f", foreground="#fecaca")
    tree.tag_configure("ok", background="#0f3d2e", foreground="#a7f3d0")


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
