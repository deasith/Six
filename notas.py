"""
App de Notas - una aplicacion simple para anotar cosas.

Hecha con Python y Tkinter (que viene incluido con Python).
Las notas se guardan automaticamente en el archivo 'notas.json',
asi que no se pierden al cerrar el programa.

Como ejecutarla:
    python3 notas.py
"""

import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog

# Archivo donde se guardan las notas (queda junto a este programa)
ARCHIVO_NOTAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notas.json")


def cargar_notas():
    """Lee las notas guardadas en el archivo. Si no existe, devuelve una lista vacia."""
    if os.path.exists(ARCHIVO_NOTAS):
        try:
            with open(ARCHIVO_NOTAS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def guardar_notas(notas):
    """Guarda la lista de notas en el archivo."""
    with open(ARCHIVO_NOTAS, "w", encoding="utf-8") as f:
        json.dump(notas, f, ensure_ascii=False, indent=2)


class AppNotas:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Mis Notas")
        self.ventana.geometry("620x420")
        self.ventana.minsize(480, 320)

        self.notas = cargar_notas()

        # ----- Barra superior con el titulo y los botones -----
        barra = tk.Frame(ventana, bg="#2c3e50", pady=10)
        barra.pack(fill=tk.X)

        tk.Label(
            barra, text="📝 Mis Notas", bg="#2c3e50", fg="white",
            font=("Arial", 16, "bold"),
        ).pack(side=tk.LEFT, padx=15)

        tk.Button(barra, text="Nueva", command=self.nueva_nota,
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                  relief=tk.FLAT, padx=12, pady=4).pack(side=tk.RIGHT, padx=(0, 15))
        tk.Button(barra, text="Editar", command=self.editar_nota,
                  bg="#2980b9", fg="white", font=("Arial", 10, "bold"),
                  relief=tk.FLAT, padx=12, pady=4).pack(side=tk.RIGHT, padx=5)
        tk.Button(barra, text="Borrar", command=self.borrar_nota,
                  bg="#c0392b", fg="white", font=("Arial", 10, "bold"),
                  relief=tk.FLAT, padx=12, pady=4).pack(side=tk.RIGHT, padx=5)

        # ----- Lista de notas (con barra de desplazamiento) -----
        marco = tk.Frame(ventana, padx=15, pady=15)
        marco.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(marco)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lista = tk.Listbox(
            marco, font=("Arial", 12), yscrollcommand=scrollbar.set,
            selectbackground="#3498db", activestyle="none",
        )
        self.lista.pack(fill=tk.BOTH, expand=True)
        self.lista.bind("<Double-Button-1>", lambda e: self.editar_nota())
        scrollbar.config(command=self.lista.yview)

        self.refrescar_lista()

    def refrescar_lista(self):
        """Vuelve a dibujar la lista con las notas actuales."""
        self.lista.delete(0, tk.END)
        if not self.notas:
            self.lista.insert(tk.END, "  (No hay notas todavia. Pulsa 'Nueva' para empezar)")
        else:
            for nota in self.notas:
                self.lista.insert(tk.END, "  • " + nota)

    def nueva_nota(self):
        texto = simpledialog.askstring("Nueva nota", "Escribe tu nota:", parent=self.ventana)
        if texto and texto.strip():
            self.notas.append(texto.strip())
            guardar_notas(self.notas)
            self.refrescar_lista()

    def _indice_seleccionado(self):
        """Devuelve el indice de la nota seleccionada, o None si no hay ninguna valida."""
        if not self.notas:
            return None
        seleccion = self.lista.curselection()
        if not seleccion:
            messagebox.showinfo("Aviso", "Primero selecciona una nota de la lista.")
            return None
        return seleccion[0]

    def editar_nota(self):
        indice = self._indice_seleccionado()
        if indice is None:
            return
        nuevo = simpledialog.askstring(
            "Editar nota", "Modifica tu nota:",
            initialvalue=self.notas[indice], parent=self.ventana,
        )
        if nuevo and nuevo.strip():
            self.notas[indice] = nuevo.strip()
            guardar_notas(self.notas)
            self.refrescar_lista()

    def borrar_nota(self):
        indice = self._indice_seleccionado()
        if indice is None:
            return
        if messagebox.askyesno("Borrar", "¿Seguro que quieres borrar esta nota?"):
            self.notas.pop(indice)
            guardar_notas(self.notas)
            self.refrescar_lista()


def main():
    ventana = tk.Tk()
    AppNotas(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()
