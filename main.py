"""
App de Notas para tablet/celular Android - hecha con Python y Kivy.
Version bonita con fecha/hora en cada nota y contador de notas.

Este es el archivo principal que Buildozer usa para crear el .apk.
Se llama 'main.py' obligatoriamente.

Como probarla en tu computador Linux:
    python3 main.py
"""

import datetime
import json
import os

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

# ---- Paleta de colores (R, G, B, transparencia) de 0 a 1 ----
FONDO       = (0.086, 0.075, 0.165, 1)
CABECERA    = (0.427, 0.298, 0.855, 1)
ACCENT      = (0.678, 0.361, 0.933, 1)
CARD        = (0.145, 0.129, 0.243, 1)
BORRAR      = (0.878, 0.353, 0.451, 1)
TEXTO       = (0.93, 0.93, 0.97, 1)
TEXTO_TENUE = (0.65, 0.62, 0.78, 1)

MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]

Window.clearcolor = FONDO


def fecha_ahora():
    """Devuelve la fecha y hora actual en texto, por ejemplo '24 jul 2026, 15:30'."""
    ahora = datetime.datetime.now()
    return f"{ahora.day} {MESES[ahora.month - 1]} {ahora.year}, {ahora.hour:02d}:{ahora.minute:02d}"


class Tarjeta(BoxLayout):
    """Un contenedor con fondo de color y esquinas redondeadas."""

    def __init__(self, color=CARD, radio=18, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*color)
            self._rect = RoundedRectangle(radius=[radio])
        self.bind(pos=self._actualizar, size=self._actualizar)

    def _actualizar(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class BotonRedondo(Button):
    """Un boton con color de fondo y esquinas redondeadas."""

    def __init__(self, color=ACCENT, radio=16, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self._base = color
        with self.canvas.before:
            self._color = Color(*color)
            self._rect = RoundedRectangle(radius=[radio])
        self.bind(pos=self._actualizar, size=self._actualizar, state=self._al_pulsar)

    def _actualizar(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _al_pulsar(self, *args):
        factor = 0.75 if self.state == "down" else 1.0
        self._color.rgba = (self._base[0] * factor, self._base[1] * factor,
                            self._base[2] * factor, 1)


class AppNotas(App):
    def build(self):
        self.title = "Mis Notas"
        self.archivo = os.path.join(self.user_data_dir, "notas.json")
        self.notas = self.cargar_notas()

        raiz = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14))

        # ---- Cabecera con titulo y contador de notas ----
        cabecera = Tarjeta(color=CABECERA, radio=22, size_hint_y=None, height=dp(64))
        self.titulo = Label(
            markup=True, font_size="24sp", color=(1, 1, 1, 1),
            halign="center", valign="middle",
        )
        cabecera.add_widget(self.titulo)
        raiz.add_widget(cabecera)

        # ---- Fila para escribir una nota nueva ----
        fila = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10))

        caja_entrada = Tarjeta(color=CARD, radio=16, padding=(dp(14), 0))
        self.entrada = TextInput(
            hint_text="Escribe una nota...", multiline=False,
            font_size="17sp", background_normal="", background_active="",
            background_color=(0, 0, 0, 0), foreground_color=TEXTO,
            cursor_color=ACCENT, hint_text_color=TEXTO_TENUE,
            padding=(0, dp(14)),
        )
        self.entrada.bind(on_text_validate=lambda w: self.agregar_nota())
        caja_entrada.add_widget(self.entrada)
        fila.add_widget(caja_entrada)

        boton_add = BotonRedondo(
            text="+", color=ACCENT, radio=16, font_size="28sp", bold=True,
            size_hint_x=None, width=dp(60),
        )
        boton_add.bind(on_release=lambda w: self.agregar_nota())
        fila.add_widget(boton_add)
        raiz.add_widget(fila)

        # ---- Lista de notas con scroll ----
        scroll = ScrollView()
        self.lista = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(10),
            padding=(0, dp(4)),
        )
        self.lista.bind(minimum_height=self.lista.setter("height"))
        scroll.add_widget(self.lista)
        raiz.add_widget(scroll)

        self.refrescar_lista()
        return raiz

    def cargar_notas(self):
        if not os.path.exists(self.archivo):
            return []
        try:
            with open(self.archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
        # Convierte notas antiguas (solo texto) al nuevo formato con fecha
        notas = []
        for nota in datos:
            if isinstance(nota, str):
                notas.append({"texto": nota, "fecha": ""})
            else:
                notas.append(nota)
        return notas

    def guardar_notas(self):
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(self.notas, f, ensure_ascii=False, indent=2)

    def refrescar_lista(self):
        # Actualiza el contador de la cabecera
        cantidad = len(self.notas)
        etiqueta = "nota" if cantidad == 1 else "notas"
        self.titulo.text = (
            f"[b]Mis Notas[/b]  "
            f"[size=15sp][color=e0d4ff]({cantidad} {etiqueta})[/color][/size]"
        )

        self.lista.clear_widgets()
        if not self.notas:
            self.lista.add_widget(Label(
                text="Aun no tienes notas.\nEscribe una arriba y pulsa  +",
                halign="center", valign="middle", size_hint_y=None, height=dp(90),
                color=TEXTO_TENUE, font_size="16sp",
            ))
            return
        for indice, nota in enumerate(self.notas):
            self.lista.add_widget(self.crear_tarjeta(indice, nota))

    def crear_tarjeta(self, indice, nota):
        """Tarjeta redondeada con el texto, la fecha debajo y un boton para borrar."""
        tarjeta = Tarjeta(color=CARD, radio=16, size_hint_y=None, height=dp(76),
                          padding=(dp(16), dp(8)), spacing=dp(8))

        # Columna con el texto arriba y la fecha abajo
        columna = BoxLayout(orientation="vertical", spacing=dp(2))

        etiqueta = Label(
            text=nota.get("texto", ""), halign="left", valign="middle",
            font_size="17sp", color=TEXTO,
        )
        etiqueta.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        columna.add_widget(etiqueta)

        fecha_texto = nota.get("fecha", "")
        etiqueta_fecha = Label(
            text=("🕒 " + fecha_texto) if fecha_texto else "",
            halign="left", valign="middle", font_size="12sp",
            color=TEXTO_TENUE, size_hint_y=None, height=dp(18),
        )
        etiqueta_fecha.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        columna.add_widget(etiqueta_fecha)

        tarjeta.add_widget(columna)

        boton_borrar = BotonRedondo(
            text="X", color=BORRAR, radio=22, font_size="18sp", bold=True,
            size_hint_x=None, width=dp(44),
        )
        boton_borrar.bind(on_release=lambda w: self.borrar_nota(indice))
        tarjeta.add_widget(boton_borrar)
        return tarjeta

    def agregar_nota(self):
        texto = self.entrada.text.strip()
        if texto:
            self.notas.append({"texto": texto, "fecha": fecha_ahora()})
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
