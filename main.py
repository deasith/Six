"""
App de Notas para tablet/celular Android - hecha con Python y Kivy.

Este es el archivo principal que Buildozer usa para crear el .apk.
Se llama 'main.py' obligatoriamente (Buildozer lo busca con ese nombre).

Como probarla en tu computador Linux:
    python3 main.py

Las notas se guardan solas y no se pierden al cerrar la app.
"""

import json
import os

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

# Colores (formato R, G, B, transparencia) de 0 a 1
COLOR_FONDO = (0.17, 0.24, 0.31, 1)
COLOR_VERDE = (0.15, 0.68, 0.37, 1)
COLOR_ROJO = (0.75, 0.22, 0.17, 1)
COLOR_TARJETA = (0.20, 0.29, 0.37, 1)

# En el computador la ventana se ve como celular vertical (en la tablet ocupa todo)
Window.clearcolor = COLOR_FONDO


class AppNotas(App):
    def build(self):
        self.title = "Mis Notas"

        # Archivo donde se guardan las notas.
        # user_data_dir es una carpeta que funciona tanto en PC como en Android.
        self.archivo = os.path.join(self.user_data_dir, "notas.json")
        self.notas = self.cargar_notas()

        # Contenedor principal (vertical)
        raiz = BoxLayout(orientation="vertical", padding=12, spacing=10)

        # Titulo arriba
        raiz.add_widget(Label(
            text="[b]Mis Notas[/b]", markup=True, font_size="26sp",
            size_hint_y=None, height=50,
        ))

        # Fila para escribir una nota nueva
        fila = BoxLayout(size_hint_y=None, height=50, spacing=8)
        self.entrada = TextInput(
            hint_text="Escribe una nota...", multiline=False,
            font_size="18sp", padding=(10, 12),
        )
        self.entrada.bind(on_text_validate=lambda w: self.agregar_nota())
        boton_add = Button(
            text="Agregar", size_hint_x=None, width=110,
            background_normal="", background_color=COLOR_VERDE, bold=True,
        )
        boton_add.bind(on_release=lambda w: self.agregar_nota())
        fila.add_widget(self.entrada)
        fila.add_widget(boton_add)
        raiz.add_widget(fila)

        # Lista de notas con scroll
        scroll = ScrollView()
        self.lista = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=8, padding=(0, 4),
        )
        self.lista.bind(minimum_height=self.lista.setter("height"))
        scroll.add_widget(self.lista)
        raiz.add_widget(scroll)

        self.refrescar_lista()
        return raiz

    def cargar_notas(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def guardar_notas(self):
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(self.notas, f, ensure_ascii=False, indent=2)

    def refrescar_lista(self):
        self.lista.clear_widgets()
        if not self.notas:
            self.lista.add_widget(Label(
                text="No hay notas todavia.\nEscribe una arriba y pulsa Agregar.",
                halign="center", size_hint_y=None, height=80, color=(1, 1, 1, 0.6),
            ))
            return
        for indice, nota in enumerate(self.notas):
            self.lista.add_widget(self.crear_tarjeta(indice, nota))

    def crear_tarjeta(self, indice, texto):
        """Crea una fila con el texto de la nota y un boton para borrarla."""
        tarjeta = BoxLayout(size_hint_y=None, height=60, spacing=6, padding=(8, 0))
        tarjeta.add_widget(Label(
            text=texto, halign="left", valign="middle", font_size="17sp",
            text_size=(Window.width - 130, None),
        ))
        boton_borrar = Button(
            text="X", size_hint_x=None, width=54,
            background_normal="", background_color=COLOR_ROJO, bold=True,
        )
        boton_borrar.bind(on_release=lambda w: self.borrar_nota(indice))
        tarjeta.add_widget(boton_borrar)
        return tarjeta

    def agregar_nota(self):
        texto = self.entrada.text.strip()
        if texto:
            self.notas.append(texto)
            self.guardar_notas()
            self.entrada.text = ""
            self.refrescar_lista()

    def borrar_nota(self, indice):
        if 0 <= indice < len(self.notas):
            self.notas.pop(indice)
            self.guardar_notas()
            self.refrescar_lista()


if __name__ == "__main__":
    AppNotas().run()
